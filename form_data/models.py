from django.db import models

class FormData(models.Model):
    form_name = models.CharField(max_length=255 , default='gxi_form')
    submission_data = models.JSONField()
    cv_upload = models.FileField(upload_to='cv_uploads/', blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    #### Microsoft team #####
    candidate_email = models.EmailField(blank=True, null=True)
    interviewer_email = models.EmailField(blank=True, null=True)
    meeting_link = models.URLField(blank=True, null=True)
    meeting_start = models.DateTimeField(blank=True, null=True)
    meeting_end = models.DateTimeField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['form_name']),
            models.Index(fields=['submitted_at']),
            models.Index(fields=['candidate_email']),
        ]
        ordering = ['-submitted_at']


    def __str__(self):
        return f"{self.form_name} submitted at {self.submitted_at}"
