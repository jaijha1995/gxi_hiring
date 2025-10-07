from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import GoogleSheetSerializer
from .models import GoogleSheet
from restserver.utils import fetch_sheet_data, get_sheet_names

class GoogleSheetListView(APIView):
    """ List all saved Google Sheets and add new ones """
    def get(self, request):
        sheets = GoogleSheet.objects.all()
        serializer = GoogleSheetSerializer(sheets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = GoogleSheetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoogleSheetDataView(APIView):
    """ Fetch all data for a given Google Sheet ID """
    def get(self, request, sheet_id):
        try:
            sheet = GoogleSheet.objects.get(id=sheet_id)
        except GoogleSheet.DoesNotExist:
            return Response({"error": "Google Sheet not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Fetch sheet names
            sheet_names = get_sheet_names(sheet.spreadsheet_id)
            if not sheet_names:
                return Response({"error": "No sheet tabs found"}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch data for the first sheet tab
            data = fetch_sheet_data(sheet.spreadsheet_id, sheet_name=sheet_names[0])

            return Response({
                "sheet": sheet.name or sheet.spreadsheet_id,
                "sheet_name": sheet_names[0],
                "data": data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)