# from rest_framework import serializers
# from .models import ApplicationForm, ApplicationStatusHistory as FormAction

# class FormActionSerializer(serializers.ModelSerializer):
#     action_by = serializers.StringRelatedField(read_only=True)

#     class Meta:
#         model = FormAction
#         fields = "__all__"

# class ApplicationFormSerializer(serializers.ModelSerializer):
#     actions = FormActionSerializer(many=True, read_only=True)
#     assigned_to = serializers.PrimaryKeyRelatedField(read_only=True)

#     class Meta:
#         model = ApplicationForm
#         fields = "__all__"
#         read_only_fields = ["last_action_by","last_action_at","created_at","updated_at","actions"]


# candidate_form/serializers.py
# candidate_form/serializers.py
from rest_framework import serializers
from django.utils import timezone
from .models import ApplicationForm, ApplicationStatusHistory
from superadmin.models import UserProfile

# --- USER PROFILE SERIALIZER ---
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        # adjust these fields to match your UserProfile model
        fields = ["id", "full_name", "email", "role", "phone_number"]
        read_only_fields = fields

class ApplicationStatusHistorySerializer(serializers.ModelSerializer):
    # show a readable representation for action_by
    action_by_display = serializers.StringRelatedField(source="action_by", read_only=True)
    action_by = UserProfileSerializer(read_only=True)
    action_by_id = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.all(), source="action_by", write_only=True, required=False
    )

    class Meta:
        model = ApplicationStatusHistory
        fields = "__all__"
        read_only_fields = ["id", "created_at", "action_by_display"]

    def create(self, validated_data):
        # If action_by wasn't supplied, attempt to use request.user's UserProfile
        action_by = validated_data.get("action_by", None)
        request = self.context.get("request", None)
        if not action_by and request and getattr(request, "user", None) and request.user.is_authenticated:
            # try to find a matching UserProfile
            try:
                # common pattern: UserProfile has OneToOneField/ForeignKey to auth user named 'user'
                profile = UserProfile.objects.get(user=request.user)
            except Exception:
                # fallback: try to get a UserProfile with same pk as request.user.pk
                try:
                    profile = UserProfile.objects.get(pk=request.user.pk)
                except Exception:
                    profile = None
            if profile:
                validated_data["action_by"] = profile
        # ensure created_at is set if needed (model default handles it)
        return super().create(validated_data)

class ApplicationFormSerializer(serializers.ModelSerializer):
    submitted_by = UserProfileSerializer(read_only=True)
    actions = ApplicationStatusHistorySerializer(many=True, read_only=True)
    assigned_to_display = serializers.SerializerMethodField()
    last_action_by_display = serializers.SerializerMethodField()

    class Meta:
        model = ApplicationForm
        fields = [
            "id",                   # first
            "form_type",
            "form_data",            # after form_type
            "submitted_by",         # full details of submitted_by
            "current_phase",
            "status",
            "assigned_to",
            "assigned_to_display",
            "last_action_by",
            "last_action_by_display",
            "last_action_at",
            "actions",              # history after main fields
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "submitted_by",
            "last_action_at",
            "actions",
            "created_at",
            "updated_at",
        ]

    def get_assigned_to_display(self, obj):
        if obj.assigned_to:
            return f"{obj.assigned_to.username} ({obj.assigned_to.email})"
        return None

    def get_last_action_by_display(self, obj):
        if obj.last_action_by:
            return f"{obj.last_action_by.username} ({obj.last_action_by.email})"
        return None

# class ApplicationFormSerializer(serializers.ModelSerializer):
#     # action_by = UserProfileSerializer(read_only=True)
#     # # submitted_by_display = serializers.StringRelatedField(source="submitted_by", read_only=True)
#     # submitted_by_id = serializers.PrimaryKeyRelatedField(
#     #     queryset=UserProfile.objects.all(), source="submitted_by", write_only=True, required=False
#     # )

#     # assigned_to = serializers.PrimaryKeyRelatedField(read_only=True)
#     assigned_to_display = serializers.StringRelatedField(source="assigned_to", read_only=True)

#     last_action_by_display = serializers.StringRelatedField(source="last_action_by", read_only=True)

#     # actions = ApplicationStatusHistorySerializer(many=True, read_only=True)

#     submitted_by = UserProfileSerializer(read_only=True)
#     # if you want to allow setting submitted_by by id on create/update:
#     submitted_by_id = serializers.PrimaryKeyRelatedField(
#         queryset=UserProfile.objects.all(), source="submitted_by", write_only=True, required=False
#     )

#     # keep nested actions (each action contains action_by as UserProfile)
#     actions = ApplicationStatusHistorySerializer(many=True, read_only=True)

#     # optional display helpers for auth user fields
#     # assigned_to_display = serializers.SerializerMethodField()
#     # last_action_by_display = serializers.SerializerMethodField()

#     class Meta:
#         model = ApplicationForm
#         # Explicit fields preferred over "__all__" for control
#         fields = "__all__"
#         read_only_fields = [
#             "id",
#             "created_at",
#             "updated_at",
#             "submitted_by_display",
#             "last_action_by_display",
#             "last_action_at",
#             "actions",
#         ]
#         extra_kwargs = {
#             "form_data": {"required": False},
#             "status": {"required": False},
#             "current_phase": {"required": False},
#         }

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # lazily set assigned_to queryset to AUTH_USER_MODEL
#         from django.contrib.auth import get_user_model
#         self.fields["assigned_to"].queryset = get_user_model().objects.all()

#     def create(self, validated_data):
#         # If submitted_by not passed, attempt to set it from request.user -> UserProfile
#         request = self.context.get("request", None)
#         submitted_by = validated_data.get("submitted_by", None)
#         if not submitted_by and request and getattr(request, "user", None) and request.user.is_authenticated:
#             try:
#                 profile = UserProfile.objects.get(user=request.user)
#             except Exception:
#                 try:
#                     profile = UserProfile.objects.get(pk=request.user.pk)
#                 except Exception:
#                     profile = None
#             if profile:
#                 validated_data["submitted_by"] = profile

#         instance = super().create(validated_data)

#         # create initial history action if none exists
#         from .models import ACTION_SUBMITTED
#         try:
#             ApplicationStatusHistory.objects.create(
#                 submission=instance,
#                 action_by=instance.submitted_by,
#                 from_phase=None,
#                 to_phase=instance.current_phase,
#                 action=ACTION_SUBMITTED,
#                 notes="Initial submission",
#             )
#         except Exception:
#             # swallow if profile missing or other reason, not critical
#             pass

#         # populate last_action_by/at if possible
#         if instance.submitted_by:
#             # last_action_by is AUTH_USER_MODEL FK in your model; we don't have that user here necessarily.
#             # Only update last_action_at and leave last_action_by if assigned via assigned_to or action.
#             instance.last_action_at = instance.created_at
#             instance.save(update_fields=["last_action_at"])
#         return instance
