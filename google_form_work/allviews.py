from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from .models import GoogleSheet, GoogleFormResponse
from .serializers import GoogleFormResponseSerializer
from .utils import fetch_google_form_responses


class GoogleFormAllSheetsAPIView(APIView):
    def get(self, request):
        sheet_id = request.query_params.get("sheet_id", None)
        all_data = []
        total_forms_count = 0  # ✅ Global total

        # ✅ If specific sheet_id provided → filter
        sheets = GoogleSheet.objects.filter(sheet_id=sheet_id) if sheet_id else GoogleSheet.objects.all()

        for sheet in sheets:
            cache_key = f"sheet_{sheet.sheet_id}_responses"
            cached_data = cache.get(cache_key)

            if cached_data:
                responses = cached_data
            else:
                try:
                    responses = fetch_google_form_responses(sheet.sheet_id)
                    saved_responses = []
                    for r in responses:
                        response_id = r.get('Timestamp') or str(hash(frozenset(r.items())))
                        obj, _ = GoogleFormResponse.objects.get_or_create(
                            sheet=sheet,
                            response_id=response_id,
                            defaults={'data': r}
                        )
                        saved_responses.append(obj)

                    serializer = GoogleFormResponseSerializer(saved_responses, many=True)
                    responses = serializer.data

                    # Cache data for 24 hours
                    cache.set(cache_key, responses, timeout=86400)
                except Exception as e:
                    all_data.append({
                        "sheet_name": sheet.name,
                        "sheet_id": sheet.sheet_id,
                        "error": str(e)
                    })
                    continue

            # ✅ Count responses for this sheet
            sheet_count = len(responses)
            total_forms_count += sheet_count

            sheet_data = {
                "sheet_name": sheet.name,
                "sheet_id": sheet.sheet_id,
                "total_responses": sheet_count,
                "responses": responses
            }

            all_data.append(sheet_data)

        # ✅ Final response with total count
        return Response({
            "sheet_count": len(all_data),
            "total_form_fills": total_forms_count,
            "data": all_data
        }, status=status.HTTP_200_OK)
