from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import CandidateDetails
from .serializers import CandidateDetailsSerializer

class CandidateDetailsView(APIView):

    def get(self, request, typeform_answer_id=None):
        if typeform_answer_id:
            # Filter by TypeformAnswer ID
            candidates = CandidateDetails.objects.filter(typeform_answer_id=typeform_answer_id)
            if not candidates.exists():
                return Response(
                    {"error": f"No candidates found for TypeformAnswer ID {typeform_answer_id}."},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Return all candidates
            candidates = CandidateDetails.objects.all()

        serializer = CandidateDetailsSerializer(candidates, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, typeform_answer_id=None):
        typeform_answer_id = request.data.get('TypeformAnswer')
        if typeform_answer_id:
            candidates = CandidateDetails.objects.filter(TypeformAnswer_id=typeform_answer_id)  # Correct field name
            if not candidates.exists():
                return Response(
                    {"error": f"No candidates found for TypeformAnswer ID {typeform_answer_id}."},
                    status=status.HTTP_404_NOT_FOUND
                )

            updated_candidates = []
            for candidate in candidates:
                if candidate.current_status == 'scouting':
                    candidate.current_status = 'ongoing'
                    candidate.interview_date = request.data.get('interview_date', candidate.interview_date)
                    candidate.save()
                    updated_candidates.append(candidate)

            if not updated_candidates:
                return Response(
                    {"message": "No candidates were updated. They might not be in 'scouting' status."},
                    status=status.HTTP_200_OK
                )

            serializer = CandidateDetailsSerializer(updated_candidates, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import CandidateDetails
from .serializers import CandidateDetailsSerializer


class CandidateListView(APIView):
    def get(self, request):
        candidates = CandidateDetails.objects.all().order_by('-created_at')
        serializer = CandidateDetailsSerializer(candidates, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
