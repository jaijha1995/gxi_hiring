from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from .models import FormData
from .serializers import FormDataSerializer


class FormDataAPIView(APIView):
    def get(self, request, pk=None):
        try:
            if pk:
                form = FormData.objects.filter(id=pk).first()
                if not form:
                    return Response(
                        {"status": "error", "message": "Record not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
                serializer = FormDataSerializer(form)
                return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)

            # Filters
            search_query = request.query_params.get('search', None)
            form_name = request.query_params.get('form_name', None)
            sort_by = request.query_params.get('sort_by', '-submitted_at')

            forms = FormData.objects.all()

            if form_name:
                forms = forms.filter(form_name__icontains=form_name)

            if search_query:
                forms = forms.filter(
                    Q(form_name__icontains=search_query) |
                    Q(submission_data__icontains=search_query)
                )

            # Sorting
            valid_sort_fields = ['form_name', 'submitted_at']
            if sort_by.lstrip('-') not in valid_sort_fields:
                sort_by = '-submitted_at'
            forms = forms.order_by(sort_by)

            # Pagination
            page = request.query_params.get('page', 1)
            page_size = int(request.query_params.get('page_size', 10))
            paginator = Paginator(forms, page_size)

            try:
                forms_page = paginator.page(page)
            except PageNotAnInteger:
                forms_page = paginator.page(1)
            except EmptyPage:
                forms_page = paginator.page(paginator.num_pages)

            serializer = FormDataSerializer(forms_page, many=True)

            return Response({
                "status": "success",
                "total_records": paginator.count,
                "total_pages": paginator.num_pages,
                "current_page": forms_page.number,
                "page_size": page_size,
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"status": "error", "message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        serializer = FormDataSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "message": "Form data saved successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": "error",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            form = FormData.objects.get(pk=pk)
        except FormData.DoesNotExist:
            return Response(
                {"status": "error", "message": "Record not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        submission_data = form.submission_data or {}
        old_status = submission_data.get("status", "Scouting")

        # Input parameters
        new_status = request.data.get("status")
        reject_reason = request.data.get("reject_reason")
        interview_date = request.data.get("interview_date")
        interview_time = request.data.get("interview_time")
        offer_letter_date = request.data.get("offer_letter_date")
        joining_date = request.data.get("joining_date")
        phase = request.data.get("phase")  # interview phase/round
        note = request.data.get("note")

        timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")

        # Default status setup
        if not old_status:
            submission_data["status"] = "Scouting"

        # === SCOUTING ===
        if old_status == "Scouting":
            if new_status == "Reject":
                if not reject_reason:
                    return Response(
                        {"status": "error", "message": "Reject reason required when rejecting from Scouting."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                submission_data.setdefault("status_history", []).append({
                    "from": old_status,
                    "to": "Reject",
                    "reason": reject_reason,
                    "updated_at": timestamp
                })
                submission_data["status"] = "Reject"
                submission_data["reject_reason"] = reject_reason

            elif new_status == "Ongoing":
                if not interview_date or not interview_time:
                    return Response(
                        {"status": "error", "message": "Interview date and time required to move from Scouting to Ongoing."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                submission_data.setdefault("status_history", []).append({
                    "from": old_status,
                    "to": "Ongoing",
                    "phase": phase or "First Round",
                    "interview_date": interview_date,
                    "interview_time": interview_time,
                    "updated_at": timestamp
                })
                submission_data["status"] = "Ongoing"
                submission_data["phase"] = phase or "First Round"

            else:
                return Response(
                    {"status": "error", "message": "Invalid transition from Scouting. Must be 'Ongoing' or 'Reject'."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # === ONGOING ===
        elif old_status == "Ongoing":
            if new_status == "Hired":
                # Candidate selected → move to Hired
                if not offer_letter_date or not joining_date:
                    return Response(
                        {"status": "error", "message": "Offer letter release date and joining date required to mark as Hired."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                submission_data.setdefault("status_history", []).append({
                    "from": "Ongoing",
                    "to": "Hired",
                    "offer_letter_date": offer_letter_date,
                    "joining_date": joining_date,
                    "updated_at": timestamp
                })
                submission_data["status"] = "Hired"
                submission_data["offer_letter_date"] = offer_letter_date
                submission_data["joining_date"] = joining_date
                submission_data["phase"] = "Final Selection"

            else:
                # Still in Ongoing — add interview rounds
                history_entry = {
                    "from": "Ongoing",
                    "to": new_status or "Ongoing",
                    "phase": phase or "Next Round",
                    "updated_at": timestamp
                }
                if interview_date:
                    history_entry["interview_date"] = interview_date
                if interview_time:
                    history_entry["interview_time"] = interview_time

                submission_data.setdefault("status_history", []).append(history_entry)
                submission_data["status"] = "Ongoing"
                submission_data["phase"] = phase or "Next Round"

        # === REJECTED ===
        elif old_status == "Reject":
            return Response(
                {"status": "error", "message": "Cannot change status after rejection."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # === HIRED ===
        elif old_status == "Hired":
            return Response(
                {"status": "error", "message": "Candidate already hired. No further changes allowed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # === Generic fallback ===
        else:
            if new_status and new_status != old_status:
                submission_data.setdefault("status_history", []).append({
                    "from": old_status,
                    "to": new_status,
                    "phase": phase,
                    "updated_at": timestamp
                })
                submission_data["status"] = new_status
                submission_data["phase"] = phase

        # --- Notes handling ---
        if note:
            submission_data.setdefault("notes_history", []).append({
                "note": note,
                "updated_at": timestamp
            })
            submission_data["note"] = note

        # --- Save ---
        form.submission_data = submission_data
        form.save()

        serializer = FormDataSerializer(form)
        return Response({
            "status": "success",
            "message": f"Status updated successfully (current: {submission_data.get('status')}, phase: {submission_data.get('phase')})",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
