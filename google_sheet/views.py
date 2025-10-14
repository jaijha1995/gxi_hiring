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


# views.py
import json
import logging
from django.utils.dateparse import parse_datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from asgiref.sync import sync_to_async
from .models import TypeformAnswer, Hiring_process
from .utils.typeform_utils import fetch_typeform_data

logger = logging.getLogger(__name__)

# FIELD MAP (same as your consumer)
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


def map_answers_grouped(answers):
    """Maps Typeform answers into grouped sections"""
    grouped = {
        "Personal_details": [],
        "Experience_details": [],
        "Education_Details": [],
        "Skills": [],
        "Maths_Skills": [],
        "Unmapped": [],
    }

    for ans in answers:
        field_id = ans.get("field", {}).get("id")
        answer_type = ans.get("type")
        value = None

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

    return grouped


class TypeformListView(APIView):
    """Fetch Typeform responses, save to DB, and return JSON"""

    def get(self, request):
        try:
            integrations = Hiring_process.objects.filter(
                integration_type="typeform", token__isnull=False
            )

            combined_data = []
            total_new = 0
            total_count_all = 0

            for integration in integrations:
                responses = fetch_typeform_data(integration.identifier, integration.token)

                if "error" in responses:
                    combined_data.append({"integration": integration.identifier, "error": responses["error"]})
                    continue

                sorted_items = sorted(
                    responses.get("items", []),
                    key=lambda x: x.get("submitted_at") or "",
                    reverse=True,  # DESC
                )

                integration_responses = []
                new_count = 0

                for item in sorted_items:
                    response_id = item.get("response_id")
                    mapped_groups = map_answers_grouped(item.get("answers", []))
                    landed_at = parse_datetime(item.get("landed_at")) if item.get("landed_at") else None
                    submitted_at = parse_datetime(item.get("submitted_at")) if item.get("submitted_at") else None

                    obj, created = TypeformAnswer.objects.get_or_create(
                        integration=integration,
                        response_id=response_id,
                        defaults={
                            "answers": mapped_groups,
                            "landed_at": landed_at,
                            "submitted_at": submitted_at,
                        },
                    )

                    if not created:
                        obj.answers = mapped_groups
                        obj.landed_at = landed_at
                        obj.submitted_at = submitted_at
                        obj.save()

                    if created:
                        new_count += 1
                        total_new += 1

                    integration_responses.append({
                        "response_id": response_id,
                        "answers": mapped_groups,
                        "landed_at": landed_at.isoformat() if landed_at else None,
                        "submitted_at": submitted_at.isoformat() if submitted_at else None,
                        "is_new": created,
                    })

                # Order the integration_responses by submitted_at DESC before appending
                integration_responses.sort(
                    key=lambda x: x["submitted_at"] or "",
                    reverse=True
                )

                combined_data.append({
                    "integration": integration.identifier,
                    "new_count": new_count,
                    "total_count": len(integration_responses),
                    "responses": integration_responses,
                })

                total_count_all += len(integration_responses)

            return Response({
                "message": "Typeform responses update (Grouped Mapping, DESC order)",
                "total_new_responses": total_new,
                "total_count_all": total_count_all,
                "data": combined_data,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in TypeformListView: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)