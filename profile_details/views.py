from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
import logging

from .models import CandidateDetails, CandidateStatusHistory, TypeformAnswer
from .serializers import CandidateDetailsSerializer, CandidateStatusHistorySerializer

logger = logging.getLogger(__name__)


# Pagination Class
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


# Candidate Details API
class CandidateDetailsAPIView(APIView):
    CACHE_TIMEOUT = 60 * 60 * 24  # 24 hours
    pagination_class = StandardResultsSetPagination  # class reference

    def get_candidate_by_response_id(self, response_id):
        """Helper function to fetch candidate via TypeformAnswer.response_id"""
        try:
            typeform_answer = TypeformAnswer.objects.get(response_id=response_id)
            candidate = CandidateDetails.objects.get(TypeformAnswer=typeform_answer)
            return candidate
        except (TypeformAnswer.DoesNotExist, CandidateDetails.DoesNotExist):
            return None

    def get(self, request, pk=None):
        """
        GET all candidates or specific candidate by response_id
        """
        if pk:
            response_id = pk
            cache_key = f"candidate_{response_id}"
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for {cache_key}")
                return Response(cached_data, status=status.HTTP_200_OK)

            candidate = self.get_candidate_by_response_id(response_id)
            if not candidate:
                return Response(
                    {"error": f"No candidate found for response_id: {response_id}"},
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = CandidateDetailsSerializer(candidate)
            cache.set(cache_key, serializer.data, self.CACHE_TIMEOUT)
            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            # List view
            status_filter = request.GET.get('status', 'all')
            page_number = request.GET.get('page', 1)
            cache_key = f"candidate_list_{status_filter}_{page_number}"

            cached_data = cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for {cache_key}")
                return Response(cached_data, status=status.HTTP_200_OK)

            candidates = CandidateDetails.objects.all().order_by('-created_at')
            if status_filter != "all":
                candidates = candidates.filter(current_status=status_filter)

            paginator = self.pagination_class()
            page = paginator.paginate_queryset(candidates, request, view=self)
            serializer = CandidateDetailsSerializer(page, many=True)
            result = paginator.get_paginated_response(serializer.data)

            cache.set(cache_key, result.data, self.CACHE_TIMEOUT)
            return result

    def post(self, request):
        """Create a new candidate (default status = scouting)"""
        serializer = CandidateDetailsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(current_status='scouting')
            self.invalidate_cache()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        """Update candidate using response_id"""
        response_id = pk
        candidate = self.get_candidate_by_response_id(response_id)
        if not candidate:
            return Response(
                {"error": f"No candidate found for response_id: {response_id}"},
                status=status.HTTP_404_NOT_FOUND
            )

        old_status = candidate.current_status

        serializer = CandidateDetailsSerializer(candidate, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            new_status = serializer.validated_data.get('current_status', old_status)

            if new_status != old_status:
                CandidateStatusHistory.objects.create(
                    candidate=candidate,
                    previous_status=old_status,
                    new_status=new_status
                )

            self.invalidate_cache(response_id)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """Delete candidate using response_id"""
        response_id = pk
        candidate = self.get_candidate_by_response_id(response_id)
        if not candidate:
            return Response(
                {"error": f"No candidate found for response_id: {response_id}"},
                status=status.HTTP_404_NOT_FOUND
            )

        candidate.delete()
        self.invalidate_cache(response_id)
        return Response({"message": "Candidate deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

    def invalidate_cache(self, response_id=None):
        """Remove cached data for LocMemCache"""
        try:
            # Manually delete candidate list caches
            if hasattr(cache, "_cache"):
                keys = [key for key in cache._cache.keys() if key.startswith("candidate_list_")]
                for key in keys:
                    cache.delete(key)

            if response_id:
                cache.delete(f"candidate_{response_id}")
        except Exception as e:
            logger.error(f"Cache invalidation failed: {str(e)}")


# Candidate Status History API
class CandidateStatusHistoryAPIView(APIView):
    CACHE_TIMEOUT = 60 * 60 * 24  # 24 hours

    def get(self, request, candidate_id=None):
        """Get history of a candidate"""
        if not candidate_id:
            return Response({"error": "candidate_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        cache_key = f"candidate_history_{candidate_id}"
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.debug(f"Cache hit for {cache_key}")
            return Response(cached_data, status=status.HTTP_200_OK)

        history = CandidateStatusHistory.objects.filter(candidate_id=candidate_id).order_by('-changed_at')
        serializer = CandidateStatusHistorySerializer(history, many=True)
        cache.set(cache_key, serializer.data, self.CACHE_TIMEOUT)
        return Response(serializer.data, status=status.HTTP_200_OK)



from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import CandidateDetails, CandidateStatusHistory
from .serializers import CandidateDetailsSerializer


class ShiftCandidateStatusView(APIView):
    def post(self, request):
        """
        Shortcut to move scouting → ongoing (default)
        """
        typeform_answer_id = request.data.get('TypeformAnswer')

        if not typeform_answer_id:
            return Response(
                {"error": "TypeformAnswer ID जरूरी है।"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch candidate
        try:
            candidate = CandidateDetails.objects.get(TypeformAnswer_id=typeform_answer_id)
        except CandidateDetails.DoesNotExist:
            return Response(
                {"error": f"इस TypeformAnswer ID ({typeform_answer_id}) से कोई candidate नहीं मिला।"},
                status=status.HTTP_404_NOT_FOUND
            )

        old_status = candidate.current_status

        if old_status != 'scouting':
            return Response(
                {"error": f"केवल 'scouting' से 'ongoing' में shift allowed है। वर्तमान स्थिति: {old_status}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update candidate
        candidate.current_status = 'ongoing'
        if 'interview_date' in request.data:
            candidate.interview_date = request.data['interview_date']
        candidate.save()

        # Save history
        CandidateStatusHistory.objects.create(
            candidate=candidate,
            previous_status=old_status,
            new_status='ongoing'
        )

        serializer = CandidateDetailsSerializer(candidate)
        return Response(
            {"message": "Candidate scouting → ongoing में shift हुआ।", "data": serializer.data},
            status=status.HTTP_200_OK
        )

    def patch(self, request):
        """
        General status shift using TypeformAnswer ID and new_status
        """
        typeform_answer_id = request.data.get('TypeformAnswer')
        new_status = request.data.get('new_status')

        if not typeform_answer_id:
            return Response(
                {"error": "TypeformAnswer ID जरूरी है।"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not new_status:
            return Response(
                {"error": "नया status (new_status) जरूरी है।"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch candidate
        try:
            candidate = CandidateDetails.objects.get(TypeformAnswer_id=typeform_answer_id)
        except CandidateDetails.DoesNotExist:
            return Response(
                {"error": f"इस TypeformAnswer ID ({typeform_answer_id}) से कोई candidate नहीं मिला।"},
                status=status.HTTP_404_NOT_FOUND
            )

        old_status = candidate.current_status

        # Allowed transitions
        allowed_transitions = {
            'scouting': ['ongoing', 'recycle'],
            'ongoing': ['hired', 'recycle'],
            'hired': [],
            'recycle': []
        }

        if new_status not in allowed_transitions.get(old_status, []):
            return Response(
                {"error": f"'{old_status}' से '{new_status}' transition allowed नहीं है। Allowed next status: {allowed_transitions.get(old_status)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validation rules
        if new_status == 'ongoing':
            if not candidate.interview_date and not request.data.get('interview_date'):
                return Response(
                    {"error": "Ongoing status के लिए interview_date जरूरी है।"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if new_status == 'hired':
            if not candidate.offer_letter_given and not request.data.get('offer_letter_given', False):
                return Response(
                    {"error": "Hired status के लिए offer_letter_given True होना चाहिए।"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not candidate.joining_date and not request.data.get('joining_date'):
                return Response(
                    {"error": "Hired status के लिए joining_date जरूरी है।"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Update fields if provided
        for field in ['interview_date', 'offer_letter_given', 'joining_date']:
            if field in request.data:
                setattr(candidate, field, request.data[field])

        # Save new status
        candidate.current_status = new_status
        candidate.save()

        # Save history
        CandidateStatusHistory.objects.create(
            candidate=candidate,
            previous_status=old_status,
            new_status=new_status
        )

        serializer = CandidateDetailsSerializer(candidate)
        return Response(
            {"message": f"Candidate '{old_status}' → '{new_status}' में shift हुआ।", "data": serializer.data},
            status=status.HTTP_200_OK
        )
