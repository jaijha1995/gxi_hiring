from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache

from .serializers import Hiring_processSerializer
from .models import Hiring_process
from django.shortcuts import get_object_or_404

from restserver.utils.utils import fetch_sheet_data, get_sheet_names
from restserver.utils.surveymonkey_utils import fetch_survey_data, get_survey_details
from restserver.utils.typeform_utils import fetch_typeform_data, get_typeform_details


class hiringprocessListView(APIView):
    def get(self, request):
        integrations = Hiring_process.objects.all()
        serializer = Hiring_processSerializer(integrations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = Hiring_processSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class HiringSheetDataView(APIView):
    CACHE_TTL = 60 * 60 * 24

    def get(self, request, integration_id):
        integration = get_object_or_404(Hiring_process, id=integration_id)

        if not integration.token:
            return Response({"error": "Token not set for this integration"}, status=status.HTTP_400_BAD_REQUEST)

        cache_key = f"integration_data_{integration_id}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        try:
            if integration.integration_type != "typeform":
                return Response({"error": "Unsupported integration type"}, status=status.HTTP_400_BAD_REQUEST)

            details = get_typeform_details(integration.identifier, integration.token)
            if "error" in details:
                return Response(details, status=status.HTTP_400_BAD_REQUEST)

            data = fetch_typeform_data(integration.identifier, integration.token)
            if "error" in data:
                return Response(data, status=status.HTTP_400_BAD_REQUEST)

            # Save only answers to DB
            responses = data.get("items", [])
            for item in responses:
                TypeformAnswer.objects.update_or_create(
                    response_id=item.get("response_id"),
                    integration=integration,
                    defaults={
                        "answers": item.get("answers", []),
                        "landed_at": item.get("landed_at"),
                        "submitted_at": item.get("submitted_at")
                    }
                )

            result = {
                "integration_id": integration.id,
                "integration_name": integration.name,
                "responses": responses
            }

            cache.set(cache_key, result, timeout=self.CACHE_TTL)
            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count

from .models import TypeformAnswer, Hiring_process
from .serializers import TypeformAnswerSerializer
from restserver.utils.typeform_utils import fetch_typeform_data


# ===========================
# FIELD NAME MAP (Categorized)
# ===========================

FIELD_NAME_MAP = {
    "Personal_details": {
        "first_name": ["GSdr0vI52V2H", "xrMAlvBbMrM9", "C66jIidCS4KW"],
        "last_name": ["K4rp3rvgL1jg", "jsHa09RwZXcj", "8WFGWnAiQbdf"],
        "phone_number": ["skkeXrAQqfxg", "XBcEyKAmDBCK", "vTNQ6dnhA1tT"],
        "email": ["PljYRNxTMKTb", "or3Akhg0oKlf", "WFvWBoE3fXey"],
        "country": ["hfVE1X2KrFdp", "BcmMmw15AJLz", "9RJE2mqcqlBH"],
        "language": ["eS4GL5ioI4bR", "41qUwfksG32C", "AhyIy57Nai1H"],
        "JOb_Resposiltes": ["JixBI29gKECC", "lBoTQOD9jtqi", "p2KSFFXGM50P"],
        "Company": ["bZmXYzNyRAar", "qosM9BaQgRiz", "9FgFAzwB9SZT"],
    },
    "Experience_details": {
        "Experience": ["ifsjUpya0xNx", "UbICuFB7QLwg", "h9YbJLKgnvz9"],
        "Notice_Period": ["QDVKrprS7Vah"],
        "Joining_date": ["3jaqKHZpq9S6"],
    },
    "Education_Details": {
        "Higest_degree": ["3hxg9RZ07fY7"],
        "Specialization": ["6g6DKtlVy9sc"],
        "University": ["xngwRnnQQfMs"],
        "Percentage": ["TGTO7FjaEGRf"],
    },
    "Skills": {
        "python": ["GaNy7pqrsc8t"],
        "python_rate": ["XsUaFdm29tiW"],
        "RDBMS": ["TOGLRSygikj7"],
        "RDBMS_rate": ["BEvfgv95crJY"],
        "Machine Learning": ["Btbfn7tEo2De"],
        "Machine Learning_rate": ["1LNTgu0cJQ4z"],
        "R_language": ["0z8VIV2t8WXX"],
        "R_language_rate": ["H5ZK7SUO53Uq"],
        "RAVE_developer": ["uyZTlo34AZgh"],
        "RAVE_developer_rate": ["iS2RHphvJ14b"],
        "Cucumber": ["CQ4ijUoGTyQM"],
        "Cucumber_rate": ["Mj5nHG6jhES4"],
        "BDD": ["yFsTMFNUPrkm"],
        "BDD_rate": ["nvyx6BuB41Ls"],
    },
    "Maths_Skills": {
        "Linear Programming": ["GtJyOWE18ugq"],
        "Linear Programming_rate": ["lrLM95WWijzt"],
        "Statistics_and_Probability": ["gGj2wCnIbgUd"],
        "Statistics_and_Probability_rate": ["iW4A9tqh0V5M"],
        "Discrete Mathematics": ["F6CGB3UfonWh"],
        "Discrete Mathematics_rate": ["X1b0Y5y3KX8D"],
    },
}


# ==============================
# GROUPED ANSWER MAPPER FUNCTION
# ==============================

def map_answers_grouped(answers):
    """Convert Typeform answer list into grouped section arrays."""
    grouped = {
        "Personal_details": [],
        "Experience_Education": [],
        "Education_Details": [],
        "Skills": [],
        "Maths_Skills": [],
        "Unmapped": [],  # fallback for unknown fields
    }

    for ans in answers:
        field_id = ans.get("field", {}).get("id")
        answer_type = ans.get("type")
        value = None

        # Determine value type
        if answer_type == "text":
            value = ans.get("text")
        elif answer_type == "phone_number":
            value = ans.get("phone_number")
        elif answer_type == "email":
            value = ans.get("email")
        elif answer_type == "choices":
            value = ans.get("choices", {}).get("labels", [])
        elif answer_type == "choice":
            value = ans.get("choice", {}).get("label")
        elif answer_type == "boolean":
            value = ans.get("boolean")
        elif answer_type == "date":
            value = ans.get("date")
        elif answer_type == "number":
            value = ans.get("number")

        # Find which group/section this field belongs to
        found = False
        for section, mapping in FIELD_NAME_MAP.items():
            for key, ids in mapping.items():
                if field_id in ids:
                    grouped[section].append({key: value})
                    found = True
                    break
            if found:
                break

        if not found:
            grouped["Unmapped"].append({field_id: value})

    # Remove empty categories for cleaner response
    grouped = {k: v for k, v in grouped.items() if v}
    return grouped


# ===========================
# MAIN API VIEW
# ===========================

class TypeformListView(APIView):

    def get(self, request, integration_id=None):
        integration_name = request.query_params.get("name")

        if integration_id is None:
            queryset = TypeformAnswer.objects.all()
            if integration_name:
                queryset = queryset.filter(integration__name__icontains=integration_name)

            all_data = []
            for ans_obj in queryset:
                ans_obj.answers = map_answers_grouped(ans_obj.answers)
                all_data.append(ans_obj)

            serializer = TypeformAnswerSerializer(all_data, many=True)

            counts_by_integration = (
                TypeformAnswer.objects.values("integration__name")
                .annotate(count=Count("id"))
                .order_by()
            )

            total_counts = {
                item["integration__name"]: item["count"]
                for item in counts_by_integration
            }

            return Response({
                "message": (
                    f"Filtered results for integration name '{integration_name}'"
                    if integration_name
                    else "All saved Typeform answers fetched successfully."
                ),
                "filtered_count": queryset.count(),
                "total_counts": total_counts,
                "status": "Scouting",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        # ========== CASE: FETCH NEW RESPONSES ==========

        try:
            integration = Hiring_process.objects.get(id=integration_id)
        except Hiring_process.DoesNotExist:
            return Response({"error": "Integration not found"}, status=status.HTTP_404_NOT_FOUND)

        data = fetch_typeform_data(integration.identifier, integration.token)
        if "error" in data:
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        answers_list = data.get("items", [])
        saved_objects = []

        for item in answers_list:
            grouped_answers = map_answers_grouped(item.get("answers", []))
            obj, created = TypeformAnswer.objects.get_or_create(
                integration=integration,
                response_id=item.get("response_id"),
                defaults={
                    "answers": grouped_answers,
                    "landed_at": item.get("landed_at"),
                    "submitted_at": item.get("submitted_at"),
                },
            )
            if created:
                saved_objects.append(obj)

        serializer = TypeformAnswerSerializer(saved_objects, many=True)

        return Response({
            "message": "Typeform responses fetched, grouped, and saved successfully.",
            "integration_id": integration_id,
            "integration_name": integration.name,
            "total_fetched": len(answers_list),
            "saved_count": len(saved_objects),
            "status": "Scouting",
            "saved_data": serializer.data
        }, status=status.HTTP_201_CREATED)
