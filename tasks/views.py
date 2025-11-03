from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Task
from .serializers import TaskSerializer


class UpdateTaskStatusAPIView(APIView):
    """
    Handles:
    - GET /tasks/ → list tasks for HR
    - GET /tasks/<pk>/ → get specific task
    - PUT /tasks/<pk>/update/ → mark task completed
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        user = request.user

        # Try to fetch by matching user directly or by email (for UserProfile)
        try:
            # If your auth user *is* UserProfile
            tasks = Task.objects.filter(user=user).order_by("-created_at")
        except Exception:
            # Otherwise try matching by email
            tasks = Task.objects.filter(user__email=user.email).order_by("-created_at")

        # If fetching one record
        if pk:
            task = get_object_or_404(tasks, pk=pk)
            serializer = TaskSerializer(task)
            return Response({
                "status": "success",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        # Optional filter ?status=pending or ?status=completed
        status_filter = request.query_params.get("status")
        if status_filter:
            if status_filter.lower() == "pending":
                tasks = tasks.filter(is_completed=False)
            elif status_filter.lower() == "completed":
                tasks = tasks.filter(is_completed=True)

        serializer = TaskSerializer(tasks, many=True)
        return Response({
            "status": "success",
            "total": tasks.count(),
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def put(self, request, pk):
        user = request.user

        # Support both direct and related matching
        try:
            task = Task.objects.get(pk=pk, user=user)
        except Task.DoesNotExist:
            task = Task.objects.filter(pk=pk, user__email=user.email).first()

        if not task:
            return Response(
                {"error": "Task not found or not assigned to you."},
                status=status.HTTP_404_NOT_FOUND
            )

        is_completed = request.data.get("is_completed")
        if is_completed is None:
            return Response(
                {"error": "is_completed field required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        task.is_completed = bool(is_completed)
        task.save(update_fields=["is_completed"])

        return Response({
            "status": "success",
            "message": "Task status updated successfully.",
            "data": TaskSerializer(task).data
        }, status=status.HTTP_200_OK)
