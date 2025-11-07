# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.files.base import ContentFile
from .models import FormData
from .serializers import FormDataSerializer
from .utils import generate_reference_style_cv


class GenerateCVAPIView(APIView):

    def post(self, request, pk):
        try:
            form = FormData.objects.get(pk=pk)
        except FormData.DoesNotExist:
            return Response(
                {"status": "error", "message": "FormData not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        submission_data = form.submission_data or {}
        if not submission_data:
            return Response(
                {"status": "error", "message": "No submission_data available"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pdf_data = generate_reference_style_cv(submission_data)
        filename = f"cv_{pk}.pdf"
        form.cv_upload.save(filename, ContentFile(pdf_data), save=True)

        serializer = FormDataSerializer(form)
        return Response(
            {
                "status": "success",
                "message": "Reference-style CV generated successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
