from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from .models import ApplicationForm, ApplicationStatusHistory as FormAction
from .serializers import ApplicationFormSerializer, FormActionSerializer
from rest_framework.permissions import IsAuthenticated

from django.db.models import Q
from superadmin.models import UserProfile

class SubmissionViewSet(viewsets.ModelViewSet):
    queryset = ApplicationForm.objects.all().select_related("assigned_to","last_action_by")
    serializer_class = ApplicationFormSerializer
    permission_classes = [IsAuthenticated]  # adapt as needed

    def perform_create(self, serializer):
        # last_action_by not set on create (could set to request.user)
        submission = serializer.save()
        # record initial action
        FormAction.objects.create(
            submission=submission,
            action_by=self.request.user if self.request.user.is_authenticated else None,
            from_phase=None,
            to_phase=submission.current_phase,
            action="submitted",
            notes="Initial submission",
            created_at=timezone.now()
        )
        submission.last_action_by = self.request.user if self.request.user.is_authenticated else None
        submission.last_action_at = timezone.now()
        submission.save()

    @action(detail=True, methods=["post"])
    def change_phase(self, request, pk=None):
        """
        Body: { "to_phase": "second_round", "notes": "...", "assigned_to": user_id (optional), "metadata": {...} }
        """
        submission = self.get_object()
        to_phase = request.data.get("to_phase")
        notes = request.data.get("notes", "")
        metadata = request.data.get("metadata", {}) or {}
        assigned_to = request.data.get("assigned_to", None)

        if not to_phase:
            return Response({"detail":"to_phase is required"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            submission = ApplicationForm.objects.select_for_update().get(pk=submission.pk)
            old = submission.current_phase
            submission.current_phase = to_phase
            if assigned_to:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                try:
                    user_obj = User.objects.get(pk=assigned_to)
                    submission.assigned_to = user_obj
                except User.DoesNotExist:
                    pass
            submission.last_action_by = request.user if request.user.is_authenticated else None
            submission.last_action_at = timezone.now()
            submission.save()

            action = FormAction.objects.create(
                submission=submission,
                action_by=request.user if request.user.is_authenticated else None,
                from_phase=old,
                to_phase=to_phase,
                action="phase_change",
                notes=notes,
                metadata=metadata
            )

        return Response({"submission": ApplicationFormSerializer(submission).data, "action": FormActionSerializer(action).data})

    @action(detail=True, methods=["post"])
    def rollback(self, request, pk=None):
        """
        Simple rollback - revert to previous action.from_phase
        """
        submission = self.get_object()
        last_action = submission.actions.order_by("-created_at").first()
        if not last_action:
            return Response({"detail":"No previous actions"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            submission = ApplicationForm.objects.select_for_update().get(pk=submission.pk)
            prev_phase = last_action.from_phase or submission.current_phase
            old_phase = submission.current_phase
            submission.current_phase = prev_phase
            submission.last_action_by = request.user if request.user.is_authenticated else None
            submission.last_action_at = timezone.now()
            submission.save()

            action = FormAction.objects.create(
                submission=submission,
                action_by=request.user if request.user.is_authenticated else None,
                from_phase=old_phase,
                to_phase=prev_phase,
                action="rollback",
                notes=f"Rollback: {request.data.get('notes','')}",
                metadata={"rollback_of_action_id": last_action.id}
            )

        return Response({"submission": ApplicationFormSerializer(submission).data, "action": FormActionSerializer(action).data})

    
    @action(detail=False, methods=["get"], url_path="my-candidates")
    def my_candidates(self, request):
        """
        Return submissions relevant to the current user.
        Logic:
          - submissions where field_by == request.user
          - OR submissions where assigned_to == request.user
        Optional query params:
          - ?current_phase=second_round
          - ?status=submitted
        """
        user = request.user

        # start from the viewset's base queryset so any global filters apply
        qs = self.filter_queryset(self.get_queryset())

        # filter to items relevant to this user (direct comparison)
        qs = qs.filter(Q(field_by=user) | Q(assigned_to=user))

        # optional additional filters from query params
        current_phase = request.query_params.get("current_phase")
        status = request.query_params.get("status")
        if current_phase:
            qs = qs.filter(current_phase=current_phase)
        if status:
            qs = qs.filter(status=status)

        # pagination support
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user

        if user.is_superuser or user.is_staff:
            return super().retrieve(request, *args, **kwargs)

        # allow if creator
        if instance.field_by == user or instance.assigned_to == user:
            return super().retrieve(request, *args, **kwargs)

        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)




