from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import FormData
from .serializers import FormDataSerializer


class FormDataAPIView(APIView):
    def get(self, request):
        try:
            # ========== 🔍 FILTERING & SEARCH ==========
            search_query = request.query_params.get('search', None)
            form_name = request.query_params.get('form_name', None)
            sort_by = request.query_params.get('sort_by', '-submitted_at')  # default latest first

            forms = FormData.objects.all()

            if form_name:
                forms = forms.filter(form_name__icontains=form_name)

            if search_query:
                forms = forms.filter(
                    Q(form_name__icontains=search_query) |
                    Q(submission_data__icontains=search_query)
                )

            # ========== 📊 SORTING ==========
            valid_sort_fields = ['form_name', 'submitted_at']
            if sort_by.lstrip('-') not in valid_sort_fields:
                sort_by = '-submitted_at'
            forms = forms.order_by(sort_by)

            # ========== 📄 PAGINATION ==========
            page = request.query_params.get('page', 1)
            page_size = int(request.query_params.get('page_size', 10))
            paginator = Paginator(forms, page_size)

            try:
                forms_page = paginator.page(page)
            except PageNotAnInteger:
                forms_page = paginator.page(1)
            except EmptyPage:
                forms_page = paginator.page(paginator.num_pages)

            serializer = FormDataSerializer(forms_page, many=True)

            # ========== ✅ SUCCESS RESPONSE ==========
            return Response({
                "status": "success",
                "total_records": paginator.count,
                "total_pages": paginator.num_pages,
                "current_page": forms_page.number,
                "page_size": page_size,
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": "error",
                "message": f"An error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        serializer = FormDataSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "message": "Form data saved successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            "status": "error",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
