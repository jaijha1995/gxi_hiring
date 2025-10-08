from rest_framework import serializers
from .models import Hiring_process

class Hiring_processSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hiring_process
        fields = ["id", "integration_type", "name", "identifier", "token","created_at"]


from rest_framework import serializers
from .models import TypeformAnswer

class TypeformAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeformAnswer
        fields = ["id", "integration", "response_id", "answers", "landed_at", "submitted_at", "created_at"]
