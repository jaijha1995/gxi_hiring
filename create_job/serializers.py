from rest_framework import serializers
from .models import Skills, Job , Department , Job_types, Location , Teams
from django.db import transaction



class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ["id", "name"]
class SkillsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skills
        fields = ['id', 'name']


class DepartmentSerializer(serializers.ModelSerializer):
    # Preferred write field
    location_ids = serializers.PrimaryKeyRelatedField(
        source="Location_types",
        many=True,
        queryset=Location.objects.all(),
        write_only=True,
        required=False
    )
    # Read field
    locations = LocationSerializer(source="Location_types", many=True, read_only=True)

    class Meta:
        model = Department
        fields = ["id", "name", "locations", "location_ids"]

    def _collect_location_objs(self, validated_data):
        """
        Return a list of Location objects from either:
          - validated_data["Location_types"] (populated when client sends `location_ids`)
          - self.initial_data["Location_types"] (raw list of IDs, legacy key)
        Raises a ValidationError if any provided id does not exist.
        """
        # Case 1: came through location_ids -> already a list of Location objs
        loc_objs = validated_data.pop("Location_types", None)
        if loc_objs is not None:
            return list(loc_objs)

        # Case 2: client sent raw "Location_types": [ids]
        raw_ids = self.initial_data.get("Location_types", None)
        if raw_ids is None:
            return None  # not provided

        if not isinstance(raw_ids, (list, tuple)):
            raise serializers.ValidationError({"Location_types": "Must be a list of IDs."})

        # Fetch and validate existence
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
            dept.Location_types.set(loc_objs)   # set from either key
        return dept

    @transaction.atomic
    def update(self, instance, validated_data):
        loc_objs = self._collect_location_objs(validated_data)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # If client explicitly provided locations (via either key), update them
        if loc_objs is not None:
            instance.Location_types.set(loc_objs)
        return instance



class TeamSerializer(serializers.ModelSerializer):
    # write with FK id
    department = serializers.PrimaryKeyRelatedField(
        source="department_types",
        queryset=Department.objects.all(),
        allow_null=True,
        required=False
    )
    # read nested department details
    department_detail = DepartmentSerializer(source="department_types", read_only=True)

    class Meta:
        model = Teams
        fields = ["id", "name", "department", "department_detail"]


class Job_typesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job_types
        fields = ['id', 'name']


class JobSerializer(serializers.ModelSerializer):
    Skills_Required = SkillsSerializer(many=True, read_only=True)
    skill_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Skills.objects.all(), write_only=True
    )

    class Meta:
        model = Job
        fields = [
            'id',
            'Job_Title',
            'Experience_In_Years',
            'Description',
            'Job_Type',
            'Job_Location',
            'no_of_opening',
            'Skills_Required',
            'skill_ids',
        ]

    def create(self, validated_data):
        skill_ids = validated_data.pop('skill_ids', [])
        job = Job.objects.create(**validated_data)
        job.Skills_Required.set(skill_ids)
        return job

    def update(self, instance, validated_data):
        skill_ids = validated_data.pop('skill_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if skill_ids is not None:
            instance.Skills_Required.set(skill_ids)
        return instance
