from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Job_types
from .serializers import Job_typesSerializer


# -------------------- SKILLS API --------------------
class jobtypesAPIView(APIView):
    def get(self, request, pk=None):
        if pk:
            skill = get_object_or_404(Job_types, pk=pk)
            serializer = Job_typesSerializer(skill)
        else:
            skills = Job_types.objects.all()
            serializer = Job_typesSerializer(skills, many=True)
        return Response({"status": "success", "data": serializer.data})

    def post(self, request):
        serializer = Job_typesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": "success", "message": "Skill created", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        skill = get_object_or_404(Job_types, pk=pk)
        serializer = jobtypesAPIView(skill, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "message": "Skill updated", "data": serializer.data})
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        skill = get_object_or_404(Job_types, pk=pk)
        skill.delete()