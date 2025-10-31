from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from .models import Job, Skills, Department, Job_types

class JobAdmin(SummernoteModelAdmin):
    summernote_fields = ('Description',)  # ✅ field to use summernote editor

admin.site.register(Job, JobAdmin)
admin.site.register(Skills)
admin.site.register(Department)
admin.site.register(Job_types)
