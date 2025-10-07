import requests
from django.conf import settings

TYPEFORM_API_BASE = "https://api.typeform.com"


def get_typeform_details(form_id):
    """
    Get Typeform form details.
    """
    headers = {
        "Authorization": f"Bearer {settings.TYPEFORM_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    url = f"{TYPEFORM_API_BASE}/forms/{form_id}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def fetch_typeform_data(form_id):
    """
    Get Typeform form responses.
    """
    headers = {
        "Authorization": f"Bearer {settings.TYPEFORM_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    url = f"{TYPEFORM_API_BASE}/forms/{form_id}/responses"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()
