from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from .models import FormData
from .serializers import FormDataSerializer


class FormDataAPIView(APIView):
    """
    API for managing FormData:
    - GET: List or single fetch
    - POST: Create new form
    - PUT: Update status / feedback / note with history tracking
    """

    # ==========================
    # GET METHOD
    # ==========================
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

    # ==========================
    # POST METHOD
    # ==========================
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

    # ==========================
    # PUT METHOD (Update status / feedback / note + history)
    # ==========================
    def put(self, request, pk):
        try:
            form = FormData.objects.get(pk=pk)
        except FormData.DoesNotExist:
            return Response(
                {"status": "error", "message": "Record not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        submission_data = form.submission_data or {}

        # Get request fields (can include any of these)
        new_status = request.data.get("status")
        feedback = request.data.get("feedback")
        note = request.data.get("note")

        # ========== 🔁 STATUS TRACKING ==========
        old_status = submission_data.get("status")
        if new_status and new_status != old_status:
            history = submission_data.get("status_history", [])
            history.append({
                "status": new_status,
                "updated_at": timezone.now().strftime("%Y-%m-%d %H:%M:%S %Z")
            })
            submission_data["status_history"] = history
            submission_data["status"] = new_status

        # ========== 📝 FEEDBACK UPDATE ==========
        if feedback:
            feedback_list = submission_data.get("feedback_history", [])
            feedback_entry = {
                "feedback": feedback,
                "updated_at": timezone.now().strftime("%Y-%m-%d %H:%M:%S %Z")
            }
            feedback_list.append(feedback_entry)
            submission_data["feedback_history"] = feedback_list
            submission_data["feedback"] = feedback

        # ========== 📘 NOTE UPDATE ==========
        if note:
            notes_list = submission_data.get("notes_history", [])
            note_entry = {
                "note": note,
                "updated_at": timezone.now().strftime("%Y-%m-%d %H:%M:%S %Z")
            }
            notes_list.append(note_entry)
            submission_data["notes_history"] = notes_list
            submission_data["note"] = note

        # Save updated JSON
        form.submission_data = submission_data
        form.save()

        serializer = FormDataSerializer(form)
        return Response({
            "status": "success",
            "message": "Data updated successfully (status / feedback / note)",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
