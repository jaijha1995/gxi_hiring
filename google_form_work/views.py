from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import GoogleSheet, GoogleFormResponse
from .serializers import GoogleSheetSerializer, GoogleFormResponseSerializer
from .utils import fetch_google_form_responses

class GoogleSheetAPIView(APIView):
    def get(self, request):
        name = request.query_params.get('name', None)
        sheets = GoogleSheet.objects.all()
        if name:
            sheets = sheets.filter(name__icontains=name)
        sheets = sheets.order_by('-created_at')
        serializer = GoogleSheetSerializer(sheets, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = GoogleSheetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



from django.core.cache import cache
class GoogleFormResponsesAPIView(APIView):
    def get(self, request, sheet_id):
        response_id = request.query_params.get("response_id", None)

        try:
            sheet = GoogleSheet.objects.get(sheet_id=sheet_id)

            # Fetch live data from Google Sheet
            responses_raw = fetch_google_form_responses(sheet.sheet_id)
            saved_responses = []

            for r in responses_raw:
                resp_id = r.get('Timestamp') or str(hash(frozenset(r.items())))
                obj, _ = GoogleFormResponse.objects.get_or_create(
                    sheet=sheet,
                    response_id=resp_id,
                    defaults={'data': r}
                )
                saved_responses.append(obj)

            serializer = GoogleFormResponseSerializer(saved_responses, many=True)
            responses = serializer.data

            # Filter by response_id if provided
            if response_id:
                responses = [r for r in responses if str(r.get("id")) == str(response_id)]

            return Response(responses, status=status.HTTP_200_OK)

        except GoogleSheet.DoesNotExist:
            return Response({'error': 'Sheet not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)