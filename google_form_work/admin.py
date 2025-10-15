from django.contrib import admin
from .models import GoogleSheet, GoogleFormResponse

# Register your models here.
admin.site.register(GoogleSheet)
admin.site.register(GoogleFormResponse)
