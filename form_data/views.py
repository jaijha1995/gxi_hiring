from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.core.mail import send_mail
from .models import FormData
from .serializers import FormDataSerializer
import requests


class FormDataAPIView(APIView):

    # 🔹 Helper function to send candidate email
    def send_status_email(self, candidate_email, candidate_name, current_status, phase=None,
                          interview_date=None, interview_time=None, joining_date=None):
        """Send email notification to candidate about their current application status."""
        if not candidate_email:
            return  # Skip if no email found

        subject = f"Update: Your Application Status - {current_status}"
        message = f"Dear {candidate_name},\n\n"
        message += f"We wanted to inform you that your application status has been updated.\n"
        message += f"➡️ Current Status: {current_status}\n"

        if phase:
            message += f"➡️ Interview Phase: {phase}\n"

        if interview_date and interview_time:
            message += f"📅 Interview Scheduled on: {interview_date} at {interview_time}\n"

        if joining_date:
            message += f"🎉 Your Joining Date: {joining_date}\n"

        message += "\nThank you for your time and interest in joining our team.\n"
        message += "Best regards,\nGXI Networks HR Team"

        try:
            send_mail(
                subject,
                message,
                '',  # Replace with DEFAULT_FROM_EMAIL
                [candidate_email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"⚠️ Email send failed to {candidate_email}: {e}")

    # ================================
    # GET METHOD
    # ================================
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

            valid_sort_fields = ['form_name', 'submitted_at']
            if sort_by.lstrip('-') not in valid_sort_fields:
                sort_by = '-submitted_at'
            forms = forms.order_by(sort_by)

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

    # ================================
    # POST METHOD
    # ================================
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

    # ================================
    # PUT METHOD (UPDATED)
    # ================================
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
        phase = request.data.get("phase")
        note = request.data.get("note")

        candidate_name = submission_data.get("Name")
        candidate_email = submission_data.get("Email")

        timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")

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

                self.send_status_email(candidate_email, candidate_name, "Reject")

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

                self.send_status_email(candidate_email, candidate_name, "Ongoing", phase, interview_date, interview_time)

            else:
                return Response(
                    {"status": "error", "message": "Invalid transition from Scouting. Must be 'Ongoing' or 'Reject'."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # === ONGOING ===
        elif old_status == "Ongoing":
            if new_status == "Hired":
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

                self.send_status_email(candidate_email, candidate_name, "Hired", "Final Selection", joining_date=joining_date)

            else:
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

                self.send_status_email(candidate_email, candidate_name, "Ongoing", phase, interview_date, interview_time)

        elif old_status == "Reject":
            return Response(
                {"status": "error", "message": "Cannot change status after rejection."},
                status=status.HTTP_400_BAD_REQUEST
            )

        elif old_status == "Hired":
            return Response(
                {"status": "error", "message": "Candidate already hired. No further changes allowed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # === Notes ===
        if note:
            submission_data.setdefault("notes_history", []).append({
                "note": note,
                "updated_at": timestamp
            })
            submission_data["note"] = note

        form.submission_data = submission_data
        form.save()

        serializer = FormDataSerializer(form)
        return Response({
            "status": "success",
            "message": f"Status updated successfully (current: {submission_data.get('status')}, phase: {submission_data.get('phase')})",
            "data": serializer.data
        }, status=status.HTTP_200_OK)




from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.core.mail import send_mail
from .serializers import FormDataSerializer
from .utils import create_teams_meeting

class ScheduleInterviewAPIView(APIView):
    def post(self, request):
        serializer = FormDataSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data

            candidate_email = data.get("candidate_email")
            interviewer_email = data.get("interviewer_email")
            start_time = data.get("meeting_start").isoformat()
            end_time = data.get("meeting_end").isoformat()

            try:
                meeting = create_teams_meeting(
                    subject=f"Interview - {data.get('form_name')}",
                    start_time=start_time,
                    end_time=end_time,
                    organizer_email=interviewer_email
                )

                meeting_link = meeting["joinWebUrl"]

                form_instance = serializer.save(submission_data=data, form_name=data.get('form_name'))

                # Send meeting link to both candidate and interviewer
                subject = "Microsoft Teams Interview Scheduled"
                message = (
                    f"Dear Candidate,\n\n"
                    f"Your interview has been scheduled.\n"
                    f"Join via Microsoft Teams using the link below:\n\n"
                    f"{meeting_link}\n\n"
                    f"Meeting Time: {start_time} to {end_time}\n\n"
                    f"Regards,\nHR Team"
                )

                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [candidate_email, interviewer_email]
                )

                return Response({
                    "message": "Meeting created successfully!",
                    "meeting_link": meeting_link
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def send_whatsapp_message(phone, name_value):
    
    url = f"https://live-mt-server.wati.io/{settings.TENANT_ID}/api/v1/sendTemplateMessage?whatsappNumber={phone}"

    payload = {
        "parameters": [
            {"name": "name", "value": name_value}
        ],
        "template_name": "otp_service",
        "broadcast_name": "otp_service_101120251049"
    }

    headers = {
        "Content-Type": "application/json-patch+json",
        "Authorization": f"Bearer {settings.WATI_API_TOKEN}"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return {
            "success": True,
            "response": response.json()
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "details": getattr(e.response, "text", None)
        }


from django.shortcuts import get_object_or_404

class SendWhatsappMessageAPIView(APIView):
    def post(self, request, form_id):
        form_data = get_object_or_404(FormData, id=form_id)
        serializer = FormDataSerializer(form_data)

        phone = serializer.data["submission_data"]["Phone"]
        # phone = "9161830835"  # for testing purpose
        name = serializer.data["submission_data"].get("Name", "there")

        message_text = f"{name}, thanks for your submission!"

        result = send_whatsapp_message(phone, message_text)

        if result["success"]:
            return Response(
                {
                    "message": "WhatsApp message sent successfully!",
                    "wati_response": result["response"],
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    "message": "Failed to send WhatsApp message",
                    "error": result["error"],
                    "detail": result.get("details")
                },
                status=status.HTTP_502_BAD_GATEWAY
            )
        
    def get(self, request):

        phone = request.query_params.get("phone")
        if not phone:
            return Response(
                {"error": "Missing 'phone' query parameter."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = self.get_whatsapp_messages(phone)

        if result["success"]:
            return Response(
                {
                    "message": "Messages fetched successfully.",
                    "data": result["response"],
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {
                    "message": "Failed to fetch WhatsApp messages.",
                    "error": result["error"],
                    "details": result.get("details"),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

    def get_whatsapp_messages(self, phone):
        url = (
            f"https://live-mt-server.wati.io/{settings.TENANT_ID}/api/v1/getMessages/{phone}"
        )

        headers = {
            "Authorization": f"Bearer {settings.WATI_API_TOKEN}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return {"success": True, "response": response.json()}
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "details": getattr(e.response, "text", None),
            }
