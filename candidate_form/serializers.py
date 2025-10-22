from rest_framework import serializers
from django.utils import timezone
from .models import ApplicationForm, ApplicationStatusHistory
from superadmin.models import UserProfile
from superadmin.serializers import UserSerializer

class ApplicationStatusHistorySerializer(serializers.ModelSerializer):
    # show a readable representation for action_by
    action_by_display = serializers.StringRelatedField(source="action_by", read_only=True)
    action_by = UserSerializer(read_only=True)
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
    submitted_by = UserSerializer(read_only=True)
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

