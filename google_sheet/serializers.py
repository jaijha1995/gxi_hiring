from rest_framework import serializers
from .models import Hiring_process, TypeformAnswer


# ============================
# Hiring Process Serializer
# ============================
class Hiring_processSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hiring_process
        fields = ["id", "integration_type", "name", "identifier", "token", "created_at"]


# ============================
# Old TypeformAnswer Serializer (JSON-based)
# ============================
# Removed 'answers' field since it doesn't exist in the model anymore
class TypeformAnswerSerializer(serializers.ModelSerializer):
    integration = Hiring_processSerializer(read_only=True)

    class Meta:
        model = TypeformAnswer
        fields = [
            "id",
            "integration",
            "response_id",
            "landed_at",
            "submitted_at",
            "created_at"
        ]


# ============================
# New TypeformAnswerDetails Serializer (Structured fields)
# ============================
class TypeformAnswerDetailsSerializer(serializers.ModelSerializer):
    integration = Hiring_processSerializer(read_only=True)

    class Meta:
        model = TypeformAnswer
        fields = [
            "id",
            "integration",
            "response_id",

            # ---------- PERSONAL DETAILS ----------
            "first_name", "last_name", "phone_number", "email",
            "country", "language", "job_responsibilities", "company",

            # ---------- EXPERIENCE / EDUCATION ----------
            "experience", "notice_period", "joining_date",

            # ---------- EDUCATION DETAILS ----------
            "highest_degree", "specialization", "university", "percentage",

            # ---------- SKILLS ----------
            "python", "python_rate",
            "rdbms", "rdbms_rate",
            "machine_learning", "machine_learning_rate",
            "r_language", "r_language_rate",
            "rave_developer", "rave_developer_rate",
            "cucumber", "cucumber_rate",
            "bdd", "bdd_rate",

            # ---------- MATHS SKILLS ----------
            "linear_programming", "linear_programming_rate",
            "statistics_probability", "statistics_probability_rate",
            "discrete_mathematics", "discrete_mathematics_rate",

            # ---------- OTHER ----------
            "unmapped_fields", "landed_at", "submitted_at", "created_at"
        ]
