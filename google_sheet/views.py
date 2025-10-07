from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache

from .serializers import Hiring_processSerializer
from .models import Hiring_process

from restserver.utils import fetch_sheet_data, get_sheet_names
from restserver.surveymonkey_utils import fetch_survey_data, get_survey_details
from restserver.typeform_utils import fetch_typeform_data, get_typeform_details


class hiringprocessListView(APIView):
    """List all saved integrations and add new ones"""

    def get(self, request):
        sheets = Hiring_process.objects.all()
        serializer = Hiring_processSerializer(sheets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = Hiring_processSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class HiringSheetDataView(APIView):
    """Fetch all data for a given Integration ID (Google Sheet, Typeform, SurveyMonkey) with caching"""

    CACHE_TTL = 60 * 60 * 24  # Cache for 5 minutes

    def get(self, request, integration_id):
        try:
            integration = Hiring_process.objects.get(id=integration_id)
        except Hiring_process.DoesNotExist:
            return Response({"error": "Integration not found"}, status=status.HTTP_404_NOT_FOUND)

        # Cache key per integration ID
        cache_key = f"integration_data_{integration_id}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        try:
            result = {}

            if integration.integration_type == "google_sheet":
                sheet_names = get_sheet_names(integration.identifier)
                if not sheet_names:
                    return Response({"error": "No sheet tabs found"}, status=status.HTTP_400_BAD_REQUEST)

                data = fetch_sheet_data(integration.identifier, sheet_name=sheet_names[0])
                result = {
                    "integration_type": "google_sheet",
                    "name": integration.name,
                    "sheet_name": sheet_names[0],
                    "data": data
                }

            elif integration.integration_type == "typeform":
                details = get_typeform_details(integration.identifier)
                data = fetch_typeform_data(integration.identifier)
                result = {
                    "integration_type": "typeform",
                    "name": integration.name,
                    "form_details": details,
                    "responses": data
                }

            elif integration.integration_type == "surveymonkey":
                details = get_survey_details(integration.identifier)
                data = fetch_survey_data(integration.identifier)
                result = {
                    "integration_type": "surveymonkey",
                    "name": integration.name,
                    "survey_details": details,
                    "responses": data
                }

            else:
                return Response({"error": "Unsupported integration type"}, status=status.HTTP_400_BAD_REQUEST)

            # Store in cache
            cache.set(cache_key, result, timeout=self.CACHE_TTL)

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
