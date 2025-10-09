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


class TypeformListView(APIView):

    def get(self, request, integration_id=None):
        integration_name = request.query_params.get("name", None)

        if integration_id is None:
            queryset = TypeformAnswer.objects.all()
            if integration_name:
                queryset = queryset.filter(
                    integration__name__icontains=integration_name
                )

            serializer = TypeformAnswerSerializer(queryset, many=True)
            counts_by_integration = (
                TypeformAnswer.objects
                .values("integration__name")
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
                    if integration_name else
                    "All saved Typeform answers fetched successfully."
                ),
                "filtered_count": queryset.count(),
                "total_counts": total_counts,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        try:
            integration = Hiring_process.objects.get(id=integration_id)
        except Hiring_process.DoesNotExist:
            return Response({"error": "Integration not found"}, status=status.HTTP_404_NOT_FOUND)

        data = fetch_typeform_data(integration.identifier, integration.token)
        print(f"Fetched data from Typeform: {data}")

        if "error" in data:
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        answers_list = data.get("responses", {}).get("items", [])
        saved_objects = []

        for item in answers_list:
            obj, created = TypeformAnswer.objects.get_or_create(
                integration=integration,
                response_id=item.get("response_id"),
                defaults={
                    "answers": item.get("answers", []),
                    "landed_at": item.get("landed_at"),
                    "submitted_at": item.get("submitted_at"),
                }
            )
            if created:
                saved_objects.append(obj)

        serializer = TypeformAnswerSerializer(saved_objects, many=True)
        return Response({
            "message": "Typeform responses fetched and saved successfully.",
            "integration_id": integration_id,
            "integration_name": integration.name,
            "total_fetched": len(answers_list),
            "saved_count": len(saved_objects),
            "typeform_raw_data": data,
            "saved_data": serializer.data
        }, status=status.HTTP_201_CREATED)
