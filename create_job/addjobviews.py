from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import add_job
from .serializers import addjobSerializer



# -------------------- SKILLS API --------------------
class AddJobAPIView(APIView):
    def get(self, request, pk=None):
        if pk:
            skill = get_object_or_404(add_job, pk=pk)
            serializer = addjobSerializer(skill)
        else:
            skills = add_job.objects.all()
            serializer = addjobSerializer(skills, many=True)
        return Response({"status": "success", "data": serializer.data})

    def post(self, request):
        serializer = addjobSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": "success", "message": "Add Jobs Successfull", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        skill = get_object_or_404(add_job, pk=pk)
        serializer = addjobSerializer(skill, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "message": "Jobs updated", "data": serializer.data})
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        skill = get_object_or_404(add_job, pk=pk)
        skill.delete()