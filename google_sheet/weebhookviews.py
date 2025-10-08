from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django_ratelimit.decorators import ratelimit
from .models import Hiring_process
from .tasks import process_integration_data
from restserver.utils.webhook_security import verify_webhook_signature


class TypeformWebhookView(APIView):

    @ratelimit(key="ip", rate="100/m", block=True)
    def post(self, request):
        signature = request.headers.get("Typeform-Signature")
        secret = "YOUR_TYPEFORM_SECRET"

        if not verify_webhook_signature(request.body, signature, secret):
            return Response({"error": "Invalid signature"}, status=status.HTTP_403_FORBIDDEN)

        form_id = request.data.get("form_id")
        integration = Hiring_process.objects.filter(integration_type="typeform", identifier=form_id).first()
        if not integration:
            return Response({"error": "Integration not found"}, status=status.HTTP_404_NOT_FOUND)

        process_integration_data.delay(integration.id)  # Asynchronous processing
        return Response({"message": "Webhook received"}, status=status.HTTP_202_ACCEPTED)


class SurveyMonkeyWebhookView(APIView):
    """Receive SurveyMonkey webhook events"""

    @ratelimit(key="ip", rate="100/m", block=True)  # Rate limit: 100 requests/min
    def post(self, request):
        signature = request.headers.get("SurveyMonkey-Signature")
        secret = "YOUR_SURVEYMONKEY_SECRET"

        if not verify_webhook_signature(request.body, signature, secret):
            return Response({"error": "Invalid signature"}, status=status.HTTP_403_FORBIDDEN)

        survey_id = request.data.get("survey_id")
        integration = Hiring_process.objects.filter(integration_type="surveymonkey", identifier=survey_id).first()
        if not integration:
            return Response({"error": "Integration not found"}, status=status.HTTP_404_NOT_FOUND)

        process_integration_data.delay(integration.id)  # Asynchronous processing
        return Response({"message": "Webhook received"}, status=status.HTTP_202_ACCEPTED)
