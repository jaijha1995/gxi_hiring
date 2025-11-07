# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404

from .models import add_job
from .serializers import addjobSerializer


class TenPerPagePagination(PageNumberPagination):
    # Default page size = 10; allow ?page_size=... to override
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 200  # safety cap


class AddJobAPIView(APIView):
    def get(self, request, pk=None):
        base_qs = (
            add_job.objects
            .select_related('teams', 'employments_types', 'posted_by', 'manager', 'hiring_manager')
            .prefetch_related('hr_team_members')
            .order_by('-created_at')  # <-- default ordering
        )

        if pk:
            job = get_object_or_404(base_qs, pk=pk)
            serializer = addjobSerializer(job)
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)

        paginator = TenPerPagePagination()
        page = paginator.paginate_queryset(base_qs, request)
        serializer = addjobSerializer(page, many=True)
        return paginator.get_paginated_response({"status": "success", "data": serializer.data})

    def post(self, request):
        serializer = addjobSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": "success", "message": "Add Jobs Successful", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        job = get_object_or_404(add_job, pk=pk)
        serializer = addjobSerializer(job, data=request.data, partial=True)  # partial update via PUT
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": "success", "message": "Job updated", "data": serializer.data},
                status=status.HTTP_200_OK
            )
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        job = get_object_or_404(add_job, pk=pk)
        serializer = addjobSerializer(job, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": "success", "message": "Job updated", "data": serializer.data},
                status=status.HTTP_200_OK
            )
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        job = get_object_or_404(add_job, pk=pk)
        job.delete()
        # 200 with a message (clearer for clients than a 204 with empty body)
        return Response({"status": "success", "message": "Job deleted"}, status=status.HTTP_200_OK)
