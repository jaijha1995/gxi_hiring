from django.contrib import admin
from .models import ApplicationForm , ApplicationStatusHistory

# Register your models here.
admin.site.register(ApplicationForm)
admin.site.register(ApplicationStatusHistory)
