from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Job, Skills
from .serializers import JobSerializer, SkillsSerializer


# -------------------- SKILLS API --------------------
class SkillsAPIView(APIView):
    def get(self, request, pk=None):
        if pk:
            skill = get_object_or_404(Skills, pk=pk)
            serializer = SkillsSerializer(skill)
        else:
            skills = Skills.objects.all()
            serializer = SkillsSerializer(skills, many=True)
        return Response({"status": "success", "data": serializer.data})

    def post(self, request):
        serializer = SkillsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": "success", "message": "Skill created", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        skill = get_object_or_404(Skills, pk=pk)
        serializer = SkillsSerializer(skill, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "message": "Skill updated", "data": serializer.data})
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        skill = get_object_or_404(Skills, pk=pk)
        skill.delete()
        return Response({"status": "success", "message": "Skill deleted"})


# -------------------- JOB API --------------------
class JobAPIView(APIView):
    def get(self, request, pk=None):
        if pk:
            job = get_object_or_404(Job, pk=pk)
            serializer = JobSerializer(job)
        else:
            jobs = Job.objects.all()
            serializer = JobSerializer(jobs, many=True)
        return Response({"status": "success", "data": serializer.data})

    def post(self, request):
        serializer = JobSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": "success", "message": "Job created", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        job = get_object_or_404(Job, pk=pk)
        serializer = JobSerializer(job, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "message": "Job updated", "data": serializer.data})
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        job = get_object_or_404(Job, pk=pk)
        job.delete()
        return Response({"status": "success", "message": "Job deleted"})
