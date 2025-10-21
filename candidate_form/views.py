# candidate_form/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import ApplicationForm, ApplicationStatusHistory
from .serializers import ApplicationFormSerializer, ApplicationStatusHistorySerializer
from superadmin.models import UserProfile
from django.utils import timezone
from django.contrib.auth import get_user_model


class IsStaffOrOwnerMixin:
    """
    Helper mixin for get_queryset style filtering: staff/superuser get all,
    normal users get only submissions where submitted_by == their UserProfile.
    """

    def _get_request_profile(self, request):
        if not request or not getattr(request, "user", None) or not request.user.is_authenticated:
            return None
        try:
            return UserProfile.objects.get(user=request.user)
        except Exception:
            try:
                return UserProfile.objects.get(pk=request.user.pk)
            except Exception:
                return None

    def filter_queryset_by_owner(self, qs, request):
        user = request.user
        if user.is_staff or user.is_superuser:
            return qs
        profile = self._get_request_profile(request)
        if profile:
            return qs.filter(submitted_by=profile)
        # if we can't map to a profile, return empty queryset for safety
        return qs.none()


# class ApplicationFormViewSet(IsStaffOrOwnerMixin, viewsets.ModelViewSet):
#     queryset = ApplicationForm.objects.all().select_related("submitted_by", "assigned_to", "last_action_by")
#     serializer_class = ApplicationFormSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         qs = super().get_queryset()
#         return self.filter_queryset_by_owner(qs, self.request)

#     def perform_create(self, serializer):
#         # try to attach submitted_by from request if not provided
#         request_profile = self._get_request_profile(self.request)
#         if request_profile and not serializer.validated_data.get("submitted_by"):
#             serializer.save(submitted_by=request_profile)
#         else:
#             serializer.save()

#     @action(detail=True, methods=["post"], url_path="add-action")
#     def add_action(self, request, pk=None):
#         """
#         POST payload example:
#         {
#           "to_phase": "second_round",
#           "action": "phase_change",
#           "notes": "good interview",
#           "metadata": {"score": 80}
#         }
#         """
#         submission = self.get_object()  # will be filtered by get_queryset -> owner/staff rules
#         data = request.data.copy()
#         data["submission"] = submission.pk

#         serializer = ApplicationStatusHistorySerializer(data=data, context={"request": request})
#         serializer.is_valid(raise_exception=True)

#         with transaction.atomic():
#             action_obj = serializer.save()
#             # Update submission fields atomically
#             changed = False
#             if action_obj.to_phase and action_obj.to_phase != submission.current_phase:
#                 submission.current_phase = action_obj.to_phase
#                 changed = True

#             # map action_obj.action_by (UserProfile) -> we don't have an auth user for last_action_by
#             # Your model's last_action_by is AUTH_USER_MODEL; we only update last_action_at and leave last_action_by if assigned.
#             submission.last_action_at = action_obj.created_at

#             if changed:
#                 submission.save(update_fields=["current_phase", "last_action_at"])
#             else:
#                 submission.save(update_fields=["last_action_at"])

#         return Response(ApplicationStatusHistorySerializer(action_obj).data, status=status.HTTP_201_CREATED)


class ApplicationFormViewSet(IsStaffOrOwnerMixin, viewsets.ModelViewSet):
    """
    ViewSet for ApplicationForm with actions:
      - add_action (generic history create)
      - change_phase (change submission.current_phase + create history)
      - rollback (revert to previous phase + create history)
      - my_candidates (list relevant submissions)
    """
    queryset = ApplicationForm.objects.all().select_related("submitted_by", "assigned_to", "last_action_by")
    serializer_class = ApplicationFormSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        return self.filter_queryset_by_owner(qs, self.request)

    def perform_create(self, serializer):
        # try to attach submitted_by from request if not provided (UserProfile)
        request_profile = self._get_request_profile(self.request)
        if request_profile and not serializer.validated_data.get("submitted_by"):
            submission = serializer.save(submitted_by=request_profile)
        else:
            submission = serializer.save()

        # create initial action (history)
        try:
            ApplicationStatusHistory.objects.create(
                submission=submission,
                action_by=request_profile,
                from_phase=None,
                to_phase=submission.current_phase,
                action="submitted",
                notes="Initial submission",
            )
        except Exception:
            # swallow to avoid failing create if profile missing
            pass

        # set last_action_by (auth user) and last_action_at
        submission.last_action_by = self.request.user if self.request.user.is_authenticated else None
        submission.last_action_at = timezone.now()
        submission.save(update_fields=["last_action_by", "last_action_at"])

    @action(detail=True, methods=["post"], url_path="add-action")
    def add_action(self, request, pk=None):
        """
        Generic endpoint to add an ApplicationStatusHistory entry.
        Expected body: { "to_phase": "...", "action": "...", "notes": "...", "metadata": {...} }
        """
        submission = self.get_object()
        data = request.data.copy()
        data["submission"] = submission.pk

        serializer = ApplicationStatusHistorySerializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            action_obj = serializer.save()
            # Update submission last_action_at (we don't have an auth user -> last_action_by remains request.user)
            submission.last_action_at = action_obj.created_at
            if request.user.is_authenticated:
                submission.last_action_by = request.user
            submission.save(update_fields=["last_action_by", "last_action_at"])

        return Response(ApplicationStatusHistorySerializer(action_obj, context={"request": request}).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="change-phase")
    def change_phase(self, request, pk=None):
        """
        Change the submission's current_phase.
        Body example:
        {
          "to_phase": "second_round",
          "notes": "Passed interview",
          "assigned_to": <auth_user_id>,    # optional
          "metadata": {...}                 # optional
        }
        """
        submission = self.get_object()
        to_phase = request.data.get("to_phase")
        notes = request.data.get("notes", "")
        metadata = request.data.get("metadata", {}) or {}
        assigned_to = request.data.get("assigned_to", None)

        if not to_phase:
            return Response({"detail": "to_phase is required"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            submission = ApplicationForm.objects.select_for_update().get(pk=submission.pk)
            old_phase = submission.current_phase
            submission.current_phase = to_phase

            # optionally assign to a user (AUTH_USER_MODEL)
            if assigned_to:
                User = get_user_model()
                try:
                    user_obj = User.objects.get(pk=assigned_to)
                    submission.assigned_to = user_obj
                except User.DoesNotExist:
                    return Response({"detail": "assigned_to user not found"}, status=status.HTTP_400_BAD_REQUEST)
            # update last action info (auth user)
            if request.user.is_authenticated:
                submission.last_action_by = request.user
            submission.last_action_at = timezone.now()
            submission.save(update_fields=["current_phase", "assigned_to", "last_action_by", "last_action_at"])

            # create history entry (action_by is UserProfile)
            profile = self._get_request_profile(request)
            action = ApplicationStatusHistory.objects.create(
                submission=submission,
                action_by=profile,
                from_phase=old_phase,
                to_phase=to_phase,
                action="phase_change",
                notes=notes,
                metadata=metadata
            )

        return Response({
            "submission": ApplicationFormSerializer(submission, context={"request": request}).data,
            "action": ApplicationStatusHistorySerializer(action, context={"request": request}).data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="rollback")
    def rollback(self, request, pk=None):
        """
        Rollback to the previous action's from_phase (if available).
        Creates a 'rollback' history entry.
        Body optional: { "notes": "reason" }
        """
        submission = self.get_object()
        last_action = submission.actions.order_by("-created_at").first()
        if not last_action:
            return Response({"detail": "No previous actions"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            submission = ApplicationForm.objects.select_for_update().get(pk=submission.pk)
            prev_phase = last_action.from_phase or submission.current_phase
            old_phase = submission.current_phase
            submission.current_phase = prev_phase

            if request.user.is_authenticated:
                submission.last_action_by = request.user
            submission.last_action_at = timezone.now()
            submission.save(update_fields=["current_phase", "last_action_by", "last_action_at"])

            profile = self._get_request_profile(request)
            action = ApplicationStatusHistory.objects.create(
                submission=submission,
                action_by=profile,
                from_phase=old_phase,
                to_phase=prev_phase,
                action="rollback",
                notes=f"Rollback: {request.data.get('notes', '')}",
                metadata={"rollback_of_action_id": last_action.id}
            )

        return Response({
            "submission": ApplicationFormSerializer(submission, context={"request": request}).data,
            "action": ApplicationStatusHistorySerializer(action, context={"request": request}).data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="my-candidates")
    def my_candidates(self, request):
        """
        List submissions relevant to the current user:
          - submissions where submitted_by == their UserProfile
          - OR submissions where assigned_to == request.user
        Supports optional ?current_phase=... & ?status=...
        """
        profile = self._get_request_profile(request)
        user = request.user

        qs = self.filter_queryset(self.get_queryset())

        if profile:
            qs = qs.filter(Q(submitted_by=profile) | Q(assigned_to=user))
        else:
            qs = qs.filter(assigned_to=user)

        current_phase = request.query_params.get("current_phase")
        status_q = request.query_params.get("status")
        if current_phase:
            qs = qs.filter(current_phase=current_phase)
        if status_q:
            qs = qs.filter(status=status_q)

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        Use IsStaffOrOwnerMixin rules to decide access:
        staff/superuser -> allowed
        owner (submitted_by -> UserProfile) OR assigned_to (auth user) -> allowed
        otherwise denied
        """
        instance = self.get_object()
        user = request.user
        profile = self._get_request_profile(request)

        if user.is_superuser or user.is_staff:
            return super().retrieve(request, *args, **kwargs)

        if (profile and instance.submitted_by_id == profile.id) or (instance.assigned_to_id == user.id):
            return super().retrieve(request, *args, **kwargs)

        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)


class ApplicationStatusHistoryViewSet(IsStaffOrOwnerMixin, viewsets.ReadOnlyModelViewSet):
    queryset = ApplicationStatusHistory.objects.select_related("action_by", "submission").all()
    serializer_class = ApplicationStatusHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        # restrict to histories for submissions visible to the user
        allowed_submissions = self.filter_queryset_by_owner(ApplicationForm.objects.all(), self.request).values_list("pk", flat=True)
        return qs.filter(submission_id__in=allowed_submissions)
