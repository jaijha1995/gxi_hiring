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
    """List all saved integrations and add new ones"""

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
    CACHE_TTL = 60 * 60 * 24  # Cache for 24 hours

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
                "responses": responses
            }

            cache.set(cache_key, result, timeout=self.CACHE_TTL)
            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import TypeformAnswer, Hiring_process
from .serializers import TypeformAnswerSerializer
from restserver.utils.typeform_utils import fetch_typeform_data

class typeformListView(APIView):

    def get(self, request, integration_id):
        try:
            integration = Hiring_process.objects.get(id=integration_id)
        except Hiring_process.DoesNotExist:
            return Response({"error": "Integration not found"}, status=status.HTTP_404_NOT_FOUND)

        # Fetch Typeform responses
        data = fetch_typeform_data(integration.identifier, integration.token)

        if "error" in data:
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        answers_list = data.get("responses", {}).get("items", [])
        saved_objects = []

        for item in answers_list:
            obj = TypeformAnswer.objects.create(
                integration=integration,
                response_id=item.get("response_id"),
                answers=item.get("answers", []),
                landed_at=item.get("landed_at"),
                submitted_at=item.get("submitted_at")
            )
            saved_objects.append(obj)

        serializer = TypeformAnswerSerializer(saved_objects, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
