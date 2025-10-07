from rest_framework import serializers
from .models import Hiring_process

class Hiring_processSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hiring_process
        fields = ["id", "integration_type", "name", "identifier", "created_at"]