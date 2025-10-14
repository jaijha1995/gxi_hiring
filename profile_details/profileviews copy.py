from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import CandidateDetails, CandidateStatusHistory
from .serializers import CandidateDetailsSerializer


class ShiftCandidateStatusView(APIView):
    """
    GET: Fetch all candidates or by TypeformAnswer ID
    POST: Shift default scouting → ongoing
    PATCH: Shift status (ongoing → hired/recycle) for TypeformAnswer ID
    """

    def get(self, request, typeform_answer_id=None):
        """
        GET candidates
        - If typeform_answer_id is provided, filter by it
        - Optional query param: ?status=ongoing/hired/recycle/scouting
        """
        status_filter = request.GET.get('status', None)

        if typeform_answer_id:
            candidates = CandidateDetails.objects.filter(TypeformAnswer__id=typeform_answer_id)
        else:
            candidates = CandidateDetails.objects.all()

        if status_filter:
            candidates = candidates.filter(current_status=status_filter)

        if not candidates.exists():
            return Response({"error": "No candidates found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = CandidateDetailsSerializer(candidates, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        typeform_answer_id = request.data.get('TypeformAnswer')
        new_status = 'ongoing'  # default for POST

        if not typeform_answer_id:
            return Response({"error": "TypeformAnswer ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        candidates = CandidateDetails.objects.filter(TypeformAnswer__id=typeform_answer_id)
        print(f"candidates: {candidates}")

        if not candidates.exists():
            return Response({"error": "No candidate found for this TypeformAnswer ID."}, status=status.HTTP_404_NOT_FOUND)

        updated_candidates = []

        for candidate in candidates:
            old_status = candidate.current_status

            # Only allow scouting → ongoing
            if old_status != 'scouting':
                continue

            interview_date = request.data.get('interview_date', getattr(candidate, 'interview_date', None))
            if not interview_date:
                continue  # skip if missing

            # Update candidate
            candidate.current_status = new_status
            candidate.interview_date = interview_date
            candidate.save()

            # Save history
            CandidateStatusHistory.objects.create(
                candidate=candidate,
                previous_status=old_status,
                new_status=new_status
            )

            updated_candidates.append(candidate)

        if not updated_candidates:
            return Response({"error": "No candidates updated. Check status or required fields."},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = CandidateDetailsSerializer(updated_candidates, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        """
        PATCH method to shift candidate status using TypeformAnswer ID
        Supports multiple candidates per TypeformAnswer
        """
        typeform_answer_id = request.data.get('TypeformAnswer')
        new_status = request.data.get('new_status')

        if not typeform_answer_id:
            return Response({"error": "TypeformAnswer ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not new_status:
            return Response({"error": "new_status is required."}, status=status.HTTP_400_BAD_REQUEST)

        candidates = CandidateDetails.objects.filter(TypeformAnswer__id=typeform_answer_id)

        if not candidates.exists():
            return Response({"error": "No candidate found for this TypeformAnswer ID."}, status=status.HTTP_404_NOT_FOUND)

        allowed_transitions = {
            'scouting': ['ongoing'],
            'ongoing': ['hired', 'recycle'],
            'hired': [],
            'recycle': []
        }

        updated_candidates = []

        for candidate in candidates:
            old_status = candidate.current_status

            if old_status != new_status and new_status not in allowed_transitions.get(old_status, []):
                continue  # skip invalid transitions

            # Additional validations
            if new_status == 'ongoing':
                interview_date = request.data.get('interview_date', getattr(candidate, 'interview_date', None))
                if not interview_date:
                    continue  # required

            if new_status == 'hired':
                offer_letter_given = request.data.get('offer_letter_given', getattr(candidate, 'offer_letter_given', False))
                joining_date = request.data.get('joining_date', getattr(candidate, 'joining_date', None))
                if not offer_letter_given or not joining_date:
                    continue  # required

            # Update candidate fields
            candidate.current_status = new_status
            if 'interview_date' in request.data:
                candidate.interview_date = request.data['interview_date']
            if 'offer_letter_given' in request.data:
                candidate.offer_letter_given = request.data['offer_letter_given']
            if 'joining_date' in request.data:
                candidate.joining_date = request.data['joining_date']

            candidate.save()

            # Save history if status changed
            if old_status != new_status:
                CandidateStatusHistory.objects.create(
                    candidate=candidate,
                    previous_status=old_status,
                    new_status=new_status
                )

            updated_candidates.append(candidate)

        if not updated_candidates:
            return Response({"error": "No candidates updated. Check status transition or required fields."},
                            status=status.HTTP_400_BAD_REQUEST)

        serializer = CandidateDetailsSerializer(updated_candidates, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
