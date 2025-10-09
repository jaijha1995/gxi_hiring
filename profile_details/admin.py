from django.contrib import admin
from .models import CandidateDetails , CandidateStatusHistory

# Register your models here.
admin.site.register(CandidateDetails)
admin.site.register(CandidateStatusHistory)
