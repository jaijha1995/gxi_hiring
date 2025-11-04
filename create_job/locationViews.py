from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Location
from .serializers import LocationSerializer



# -------------------- SKILLS API --------------------
class LocationAPIView(APIView):
    def get(self, request, pk=None):
        if pk:
            skill = get_object_or_404(Location, pk=pk)
            serializer = LocationSerializer(skill)
        else:
            skills = Location.objects.all()
            serializer = LocationSerializer(skills, many=True)
        return Response({"status": "success", "data": serializer.data})

    def post(self, request):
        serializer = LocationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": "success", "message": "Skill created", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        skill = get_object_or_404(Location, pk=pk)
        serializer = LocationSerializer(skill, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "message": "Skill updated", "data": serializer.data})
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        skill = get_object_or_404(Location, pk=pk)
        skill.delete()