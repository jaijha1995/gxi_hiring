from rest_framework import serializers
from .models import google_form

class google_formSerializer(serializers.ModelSerializer):
    class Meta:
        model = google_form
        # Fields to expose in API
        fields = ['id', 'name', 'identifier', 'created_at']
        read_only_fields = ['id', 'created_at']
