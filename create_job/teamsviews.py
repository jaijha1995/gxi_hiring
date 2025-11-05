# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Teams
from .serializers import TeamSerializer


class teamsAPIView(APIView):

    def get(self, request, pk=None):
        if pk:
            team = get_object_or_404(
                Teams.objects.select_related("department_types")
                .prefetch_related("department_types__Location_types"),
                pk=pk
            )
            serializer = TeamSerializer(team)
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)

        # List with filters
        qs = (
            Teams.objects.select_related("department_types")
            .prefetch_related("department_types__Location_types")
            .all()
        )

        # --- Filters ---
        name = request.query_params.get("name")
        if name:
            qs = qs.filter(name__icontains=name)

        location = request.query_params.get("location")  # location name (partial)
        if location:
            qs = qs.filter(department_types__Location_types__name__icontains=location)

        # Avoid duplicates when a department matches multiple locations
        qs = qs.distinct().order_by("id")

        serializer = TeamSerializer(qs, many=True)
        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = TeamSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": "success", "message": "Team created", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        team = get_object_or_404(Teams, pk=pk)
        serializer = TeamSerializer(team, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": "success", "message": "Team updated", "data": serializer.data},
                status=status.HTTP_200_OK,
            )
        return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        team = get_object_or_404(Teams, pk=pk)
        team.delete()
        return Response({"status": "success", "message": "Team deleted"}, status=status.HTTP_204_NO_CONTENT)
