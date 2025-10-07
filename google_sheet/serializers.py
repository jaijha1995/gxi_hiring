from rest_framework import serializers
from .models import GoogleSheet

class GoogleSheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoogleSheet
        fields = ["id", "name", "spreadsheet_id", "created_at"]