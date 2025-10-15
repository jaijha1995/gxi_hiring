from rest_framework import serializers
from .models import GoogleSheet, GoogleFormResponse

class GoogleSheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoogleSheet
        fields = '__all__'


class GoogleFormResponseSerializer(serializers.ModelSerializer):
    sheet = GoogleSheetSerializer(read_only=True)

    class Meta:
        model = GoogleFormResponse
        fields = '__all__'
