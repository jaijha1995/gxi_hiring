from rest_framework import serializers
from django.utils import timezone
from .models import FormData

class FormDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = FormData
        fields = "__all__"