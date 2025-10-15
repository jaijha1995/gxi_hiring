from django.db import models
from django.utils import timezone
from google_sheet.models import TypeformAnswer
from google_form_work.models import GoogleFormResponse

class CandidateDetails(models.Model):
    STATUS_CHOICES = [
        ('scouting', 'Scouting'),
        ('ongoing', 'Ongoing'),
        ('hired', 'Hired'),
        ('recycle', 'Recycle'),
    ]
    TypeformAnswer = models.ForeignKey(GoogleFormResponse, on_delete=models.CASCADE, related_name='candidates', db_index=True)
    current_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scouting', db_index=True)
    interview_date = models.DateField(null=True, blank=True)
    offer_letter_given = models.BooleanField(default=False)
    joining_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['current_status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Candidate {self.pk} - {self.current_status}"


class CandidateStatusHistory(models.Model):
    candidate = models.ForeignKey(
        CandidateDetails,
        on_delete=models.CASCADE,
        related_name='history',
        db_index=True
    )
    previous_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    changed_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['previous_status']),
            models.Index(fields=['new_status']),
        ]

    def __str__(self):
        return f"{self.previous_status} → {self.new_status} ({self.candidate_id})"
