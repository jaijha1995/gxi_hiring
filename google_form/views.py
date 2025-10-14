from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import google_form
from .serializers import google_formSerializer
from .utils import fetch_sheet_data

class googleAPIView(APIView):
    def get(self, request, id=None):
        if id:
            camera = google_form.objects.filter(id=id).first()
            if camera:
                serializer = google_formSerializer(camera)
                return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({"status": "error", "message": "address not found"}, status=status.HTTP_404_NOT_FOUND)
        camera = google_form.objects.all()
        serializer = google_formSerializer(camera, many=True)
        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request, org_id=None):
        data = request.data
        serializer = google_formSerializer(data=request.data)

        if serializer.is_valid():
            Camera = serializer.save()
            Camera.save()
            return Response({"status": "success", "data": serializer.data , "msg": "address added successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"status": "Please provide mandatory fields", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)



# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .utils import fetch_sheet_data

class GoogleFormResponsesView(APIView):
    """
    API to fetch Google Form responses from linked Google Sheet
    """
    def get(self, request, *args, **kwargs):
        sheet_id = request.query_params.get("sheet_id")
        sheet_name = request.query_params.get("sheet_name")  # optional

        if not sheet_id:
            return Response({"error": "sheet_id query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            data = fetch_sheet_data(sheet_id, sheet_name)
            return Response({"responses": data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
