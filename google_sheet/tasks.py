from celery import shared_task
from django.core.cache import cache
from .models import Hiring_process
from restserver.utils.utils import fetch_sheet_data, get_sheet_names
from restserver.utils.typeform_utils import fetch_typeform_data, get_typeform_details
from restserver.utils.surveymonkey_utils import fetch_survey_data, get_survey_details
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_integration_data(self, integration_id):
    try:
        integration = Hiring_process.objects.get(id=integration_id)
        result = {}

        if integration.integration_type == "google_sheet":
            sheet_names = get_sheet_names(integration.identifier)
            if not sheet_names:
                raise ValueError("No sheet tabs found")
            data = fetch_sheet_data(integration.identifier, sheet_name=sheet_names[0])
            result = {
                "integration_type": "google_sheet",
                "name": integration.name,
                "sheet_name": sheet_names[0],
                "data": data
            }

        elif integration.integration_type == "typeform":
            details = get_typeform_details(integration.identifier)
            data = fetch_typeform_data(integration.identifier)
            result = {
                "integration_type": "typeform",
                "name": integration.name,
                "form_details": details,
                "responses": data
            }

        elif integration.integration_type == "surveymonkey":
            details = get_survey_details(integration.identifier)
            data = fetch_survey_data(integration.identifier)
            result = {
                "integration_type": "surveymonkey",
                "name": integration.name,
                "survey_details": details,
                "responses": data
            }

        # Cache result for 24 hours
        cache_key = f"integration_data_{integration_id}"
        cache.set(cache_key, result, timeout=60 * 60 * 24)

        return {"status": "success", "integration_id": integration_id}

    except Exception as exc:
        logger.error(f"Error processing integration {integration_id}: {exc}")
        self.retry(exc=exc, countdown=10)
