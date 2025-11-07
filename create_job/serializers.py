# serializers.py
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from .models import Skills, Department, Job_types, Location, Teams, add_job
from superadmin.models import UserProfile  # role constants

User = get_user_model()


# ---------- Basic serializers ----------
class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ["id", "name"]


class SkillsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skills
        fields = ["id", "name"]


class Job_typesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job_types
        fields = ["id", "name"]


# ---------- Department (w/ M2M: Location) ----------
class DepartmentSerializer(serializers.ModelSerializer):
    # write-only ids
    location_ids = serializers.PrimaryKeyRelatedField(
        source="Location_types",
        many=True,
        queryset=Location.objects.all(),
        write_only=True,
        required=False,
    )
    # read-only nested
    locations = LocationSerializer(source="Location_types", many=True, read_only=True)

    class Meta:
        model = Department
        fields = ["id", "name", "locations", "location_ids"]

    def _collect_location_objs(self, validated_data):
        # Case 1: via location_ids (already objects)
        loc_objs = validated_data.pop("Location_types", None)
        if loc_objs is not None:
            return list(loc_objs)

        # Case 2: legacy key Location_types: [ids]
        raw_ids = self.initial_data.get("Location_types", None)
        if raw_ids is None:
            return None

        if not isinstance(raw_ids, (list, tuple)):
            raise serializers.ValidationError({"Location_types": "Must be a list of IDs."})

        qs = Location.objects.filter(id__in=raw_ids).only("id")
        found = list(qs)
        if len(found) != len(set(raw_ids)):
            found_ids = {o.id for o in found}
            missing = [i for i in raw_ids if i not in found_ids]
            raise serializers.ValidationError({"Location_types": f"Invalid IDs: {missing}"})
        return found

    def validate_name(self, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise serializers.ValidationError("Name cannot be empty or whitespace.")
        return normalized

    @transaction.atomic
    def create(self, validated_data):
        loc_objs = self._collect_location_objs(validated_data)
        dept = Department.objects.create(**validated_data)
        if loc_objs is not None:
            dept.Location_types.set(loc_objs)
        return dept

    @transaction.atomic
    def update(self, instance, validated_data):
        loc_objs = self._collect_location_objs(validated_data)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if loc_objs is not None:
            instance.Location_types.set(loc_objs)
        return instance


# ---------- Teams (people fields removed) ----------
class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teams
        fields = [
            "id",
            "name",
            "department_types",
        ]


# ---------- Lightweight user serializer (works with custom user model) ----------
class LiteUserSerializer(serializers.ModelSerializer):
    display = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "display"]

    def get_display(self, obj):
        return str(obj)


# ---------- add_job ----------
class addjobSerializer(serializers.ModelSerializer):
    # ---- write-only relation IDs (accepted on POST/PATCH, hidden in output) ----
    teams = serializers.PrimaryKeyRelatedField(
        queryset=Teams.objects.all(), allow_null=True, required=False, write_only=True
    )
    employments_types = serializers.PrimaryKeyRelatedField(
        queryset=Job_types.objects.all(), allow_null=True, required=False, write_only=True
    )
    posted_by = serializers.PrimaryKeyRelatedField(read_only=True)

    skills_required = serializers.PrimaryKeyRelatedField(
        queryset=Skills.objects.all(), many=True, required=False, write_only=True
    )

    manager = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=UserProfile.ROLE_MANAGER),
        allow_null=True, required=False, write_only=True
    )
    hiring_manager = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=UserProfile.Hiring_Manager),
        allow_null=True, required=False, write_only=True
    )
    hr_team_members = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=UserProfile.ROLE_HR),
        many=True, required=False, write_only=True
    )

    # ---- read-only detail fields (shown in responses) ----
    teams_detail = serializers.SerializerMethodField(read_only=True)
    employments_types_detail = serializers.SerializerMethodField(read_only=True)
    posted_by_detail = serializers.SerializerMethodField(read_only=True)
    manager_detail = serializers.SerializerMethodField(read_only=True)
    hiring_manager_detail = serializers.SerializerMethodField(read_only=True)
    hr_team_members_detail = serializers.SerializerMethodField(read_only=True)
    skills_details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = add_job
        fields = '__all__'
        read_only_fields = ('job_id', 'created_at', 'updated_at', 'posted_by')

    # ---------- detail getters (these fix your AttributeError) ----------
    def get_teams_detail(self, obj):
        if obj.teams_id:
            return {"id": obj.teams_id, "name": getattr(obj.teams, "name", None)}
        return None

    def get_employments_types_detail(self, obj):
        if obj.employments_types_id:
            return {"id": obj.employments_types_id, "name": getattr(obj.employments_types, "name", None)}
        return None

    def get_posted_by_detail(self, obj):
        if obj.posted_by_id:
            u = obj.posted_by
            name = getattr(u, "name", None) or getattr(u, "full_name", None) or getattr(u, "username", None) or getattr(u, "email", None)
            return {"id": obj.posted_by_id, "email": getattr(u, "email", None), "name": name}
        return None

    def get_manager_detail(self, obj):
        if obj.manager_id:
            # adjust what you want to show
            return {"id": obj.manager_id, "email": getattr(obj.manager, "email", None)}
        return None

    def get_hiring_manager_detail(self, obj):
        if obj.hiring_manager_id:
            return {"id": obj.hiring_manager_id, "email": getattr(obj.hiring_manager, "email", None)}
        return None

    def get_hr_team_members_detail(self, obj):
        if hasattr(obj, "hr_team_members"):
            return [{"id": u.id, "display": str(u)} for u in obj.hr_team_members.all()]
        return []

    def get_skills_details(self, obj):
        if hasattr(obj, "skills_required"):
            return [{"id": s.id, "name": getattr(s, "name", str(s))} for s in obj.skills_required.all()]
        return []

    # ---------- simple sanitizers ----------
    def validate_Salary_range(self, value):
        return value.strip() if isinstance(value, str) else value

    def validate_Experience_required(self, value):
        return value.strip() if isinstance(value, str) else value

    # ---------- cross-field validation ----------
    def validate(self, attrs):
        # fallback to instance for partial updates
        manager = attrs.get('manager') or getattr(self.instance, 'manager', None)
        hiring_manager = attrs.get('hiring_manager') or getattr(self.instance, 'hiring_manager', None)
        hrs = attrs.get('hr_team_members', None)

        if manager and getattr(manager, 'role', None) != UserProfile.ROLE_MANAGER:
            raise serializers.ValidationError({"manager": "Selected user is not a Manager."})

        if hiring_manager:
            if getattr(hiring_manager, 'role', None) != UserProfile.Hiring_Manager:
                raise serializers.ValidationError({"hiring_manager": "Selected user is not a HiringManager."})
            if manager and getattr(hiring_manager, 'created_by_manager_id', None) != manager.id:
                raise serializers.ValidationError({"hiring_manager": "HiringManager must be created by the selected Manager."})

        if hrs is not None:
            for hr in hrs:
                if getattr(hr, 'role', None) != UserProfile.ROLE_HR:
                    raise serializers.ValidationError({"hr_team_members": f"User {hr.id} is not an HR."})
                if manager and getattr(hr, 'created_by_manager_id', None) != manager.id:
                    raise serializers.ValidationError({"hr_team_members": f"HR {hr.id} must be created by the selected Manager."})

        return attrs

    # ---------- write hooks ----------
    def create(self, validated_data):
        # set posted_by from request user
        req = self.context.get("request")
        if req and req.user and req.user.is_authenticated:
            validated_data["posted_by"] = req.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # keep job_id immutable
        validated_data.pop("job_id", None)
        return super().update(instance, validated_data)