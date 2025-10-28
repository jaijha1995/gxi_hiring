from django.db import models

# Create your models here.

class FormData(models.Model):
    form_name = models.CharField(max_length=255 , default='gxi_form')
    submission_data = models.JSONField()
    cv_upload = models.FileField(upload_to='cv_uploads/', blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.form_name} submitted at {self.submitted_at}"
