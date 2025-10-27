from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import ApplicationForm, ApplicationStatusHistory
from .serializers import ApplicationFormSerializer, ApplicationStatusHistorySerializer
from superadmin.models import UserProfile
from superadmin.serializers import UserSerializer
from rest_framework import status


class ApplicationFormAPIView(APIView):
    # authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

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

    def get(self, request, pk=None):
        """Retrieve a single submission or list all relevant submissions"""
        # return Response({'detail': 'Not implemented'}, status=501)
        if pk:
            submission = get_object_or_404(ApplicationForm, pk=pk)
            profile = self._get_request_profile(request)
            if request.user.is_staff or request.user.is_superuser \
               or (profile and submission.submitted_by_id == profile.id) \
               or submission.assigned_to_id == request.user.id:
                serializer = ApplicationFormSerializer(submission, context={"request": request})
                return Response(serializer.data)
            return Response({"detail": "Permission denied."}, status=403)

        # list all relevant submissions
        profile = self._get_request_profile(request)
        qs = ApplicationForm.objects.all()
        if not (request.user.is_staff or request.user.is_superuser):
            if profile:
                qs = qs.filter(Q(submitted_by=profile) | Q(assigned_to=request.user))
            else:
                qs = qs.filter(assigned_to=request.user)

        current_phase = request.query_params.get("current_phase")
        status_q = request.query_params.get("status")
        if current_phase:
            qs = qs.filter(current_phase=current_phase)
        if status_q:
            qs = qs.filter(status=status_q)

        serializer = ApplicationFormSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request):
        """Create a new submission"""
        profile = self._get_request_profile(request)
        serializer = ApplicationFormSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            submission = serializer.save(submitted_by=profile if profile else None)
            # Initial history
            ApplicationStatusHistory.objects.create(
                submission=submission,
                action_by=profile,
                from_phase=None,
                to_phase=submission.current_phase,
                action="submitted",
                notes="Initial submission"
            )
            submission.last_action_by = request.user if request.user.is_authenticated else None
            submission.last_action_at = timezone.now()
            submission.save(update_fields=["last_action_by", "last_action_at"])

        return Response(ApplicationFormSerializer(submission, context={"request": request}).data, status=201)

    def put(self, request, pk=None):
        """Full update of submission"""
        if not pk:
            return Response({"detail": "Submission ID required"}, status=400)
        submission = get_object_or_404(ApplicationForm, pk=pk)
        serializer = ApplicationFormSerializer(submission, data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request, pk=None):
        """Partial update of submission"""
        if not pk:
            return Response({"detail": "Submission ID required"}, status=400)
        submission = get_object_or_404(ApplicationForm, pk=pk)
        serializer = ApplicationFormSerializer(submission, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk=None):
        """Delete a submission"""
        if not pk:
            return Response({"detail": "Submission ID required"}, status=400)
        submission = get_object_or_404(ApplicationForm, pk=pk)
        submission.delete()
        return Response({"detail": "Submission deleted successfully"}, status=204)

    @staticmethod
    def _get_submission(pk):
        return get_object_or_404(ApplicationForm, pk=pk)

    @staticmethod
    def _get_user(request, user_id):
        User = get_user_model()
        return get_object_or_404(User, pk=user_id)


class ChangePhaseAPIView(APIView):
    # authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    # permission_classes = []

    def post(self, request, pk):
        """Change phase of submission"""
        submission = get_object_or_404(ApplicationForm, pk=pk)
        to_phase = request.data.get("to_phase")
        notes = request.data.get("notes", "")
        metadata = request.data.get("metadata", {}) or {}
        assigned_to_id = request.data.get("assigned_to")

        if not to_phase:
            return Response({"detail": "to_phase is required"}, status=400)

        with transaction.atomic():
            old_phase = submission.current_phase
            submission.current_phase = to_phase

            if assigned_to_id:
                User = get_user_model()
                user_obj = get_object_or_404(User, pk=assigned_to_id)
                submission.assigned_to = user_obj

            submission.last_action_by = request.user
            submission.last_action_at = timezone.now()
            submission.save(update_fields=["current_phase", "assigned_to", "last_action_by", "last_action_at"])

            # profile = UserProfile.objects.filter(user=request.user).first()
            action = ApplicationStatusHistory.objects.create(
                submission=submission,
                # action_by=profile,
                from_phase=old_phase,
                to_phase=to_phase,
                action="phase_change",
                notes=notes,
                metadata=metadata
            )

        return Response({
            "submission": ApplicationFormSerializer(submission, context={"request": request}).data,
            "action": ApplicationStatusHistorySerializer(action, context={"request": request}).data
        })


class RollbackAPIView(APIView):
    # authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Rollback submission to previous phase"""
        submission = get_object_or_404(ApplicationForm, pk=pk)
        last_action = submission.actions.order_by("-created_at").first()
        if not last_action:
            return Response({"detail": "No previous actions"}, status=400)

        with transaction.atomic():
            prev_phase = last_action.from_phase or submission.current_phase
            old_phase = submission.current_phase
            submission.current_phase = prev_phase
            submission.last_action_by = request.user
            submission.last_action_at = timezone.now()
            submission.save(update_fields=["current_phase", "last_action_by", "last_action_at"])

            # profile = UserProfile.objects.filter(user=request.user).first()
            action = ApplicationStatusHistory.objects.create(
                submission=submission,
                # action_by=profile,
                from_phase=old_phase,
                to_phase=prev_phase,
                action="rollback",
                notes=f"Rollback: {request.data.get('notes', '')}",
                metadata={"rollback_of_action_id": last_action.id}
            )

        return Response({
            "submission": ApplicationFormSerializer(submission, context={"request": request}).data,
            "action": ApplicationStatusHistorySerializer(action, context={"request": request}).data
        })

class MyCandidatesAPIView(APIView):
    """
    - GET /api/candidates/applications/my-candidates/
        -> candidates relevant to logged-in user (submitted_by == profile OR assigned_to == auth user)
    - GET /api/candidates/applications/<int:hr_id>/my-candidates/
        -> candidates for the HR with id=hr_id (only allowed for staff/superuser)
    """
    # authentication_classes = [TokenAuthentication]  # optional: remove if you use default auth
    permission_classes = [IsAuthenticated]

    def get(self, request, hr_id=None):
        # If hr_id is provided, only allow staff/superuser to query by other HR id
        if hr_id is not None:
            if not (request.user.is_staff or request.user.is_superuser):
                return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
            # hr_id refers to UserProfile.id (your custom user model)
            hr_profile = get_object_or_404(UserProfile, id=hr_id)
            # return applications where submitted_by is that HR OR assigned_to is that HR (if assigned_to uses auth user)
            qs = ApplicationForm.objects.filter(Q(submitted_by=hr_profile) | Q(assigned_to_id=hr_profile.id)).distinct()
        else:
            # no hr_id: return candidates relevant to the logged-in user
            # request.user is a UserProfile instance in your setup (custom user model), so find profile by id
            profile = UserProfile.objects.filter(id=request.user.id).first()
            if profile:
                qs = ApplicationForm.objects.filter(Q(submitted_by=profile) | Q(assigned_to=request.user))
            else:
                qs = ApplicationForm.objects.filter(assigned_to=request.user)

        # optional filters
        current_phase = request.query_params.get("current_phase")
        status_q = request.query_params.get("status")
        if current_phase:
            qs = qs.filter(current_phase=current_phase)
        if status_q:
            qs = qs.filter(status=status_q)

        qs = qs.select_related("submitted_by", "assigned_to", "last_action_by").prefetch_related("actions")
        serializer = ApplicationFormSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
