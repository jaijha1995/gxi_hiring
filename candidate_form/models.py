from django.db import models
from django.conf import settings
from django.utils import timezone
from profile_details.models import CandidateDetails
from superadmin.models import UserProfile


# If using Postgres, you can add GinIndex below
from django.contrib.postgres.indexes import GinIndex

# Phase choices
PHASE_FIRST = "first_round"
PHASE_SECOND = "second_round"
PHASE_THIRD = "third_round"
PHASE_HIRED = "hired"
PHASE_REJECTED = "rejected"

PHASE_CHOICES = [
    (PHASE_FIRST, "First Round"),
    (PHASE_SECOND, "Second Round"),
    (PHASE_THIRD, "Third Round"),
    (PHASE_HIRED, "Hired"),
    (PHASE_REJECTED, "Rejected"),
]

STATUS_SUBMITTED = "submitted"

# Optional action choices for stricter validation
ACTION_SUBMITTED = "submitted"
ACTION_PHASE_CHANGE = "phase_change"
ACTION_ASSIGNED = "assigned"
ACTION_ROLLBACK = "rollback"
ACTION_COMMENT = "comment"

ACTION_CHOICES = [
    (ACTION_SUBMITTED, "Submitted"),
    (ACTION_PHASE_CHANGE, "Phase Change"),
    (ACTION_ASSIGNED, "Assigned"),
    (ACTION_ROLLBACK, "Rollback"),
    (ACTION_COMMENT, "Comment"),
]


class ApplicationForm(models.Model):
    submitted_by = models.ForeignKey(UserProfile, null=True, blank=True, on_delete=models.SET_NULL)
    form_type = models.CharField(max_length=150, blank=True, db_index=True, help_text="Role/form identifier (slug)")
    form_data = models.JSONField(default=dict, help_text="Raw form submission JSON")
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    current_phase = models.CharField(max_length=50, choices=PHASE_CHOICES, default=PHASE_FIRST, db_index=True)
    status = models.CharField(max_length=30, default=STATUS_SUBMITTED, db_index=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_submissions"
    )

    last_action_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="last_actions"
    )
    last_action_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["current_phase"]),
            # GinIndex on form_data requires Postgres — uncomment if using Postgres
            # GinIndex(fields=["form_data"]),
        ]

    def __str__(self):
        return f"{self.form_type or 'submission'} #{self.pk} by {self.submitted_by}"

    # convenience helpers
    def last_action(self):
        return self.actions.order_by("-created_at").first()

    def get_timeline(self):
        return self.actions.all().order_by("created_at")


class ApplicationStatusHistory(models.Model):
    """
    Immutable audit/history table for every change.
    """
    submission = models.ForeignKey(ApplicationForm, on_delete=models.CASCADE, related_name="actions")
    action_by = models.ForeignKey(UserProfile, null=True, blank=True, on_delete=models.SET_NULL)
    from_phase = models.CharField(max_length=50, choices=PHASE_CHOICES, blank=True, null=True)
    to_phase = models.CharField(max_length=50, choices=PHASE_CHOICES)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, default=ACTION_PHASE_CHANGE)
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)  # interview scores, file refs, etc.
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["submission", "created_at"]),
            models.Index(fields=["to_phase"]),
        ]

    def __str__(self):
        return f"Action {self.action} on {self.submission_id} -> {self.to_phase} by {self.action_by}"
