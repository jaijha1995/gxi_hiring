import requests
import logging

TYPEFORM_API_BASE = "https://api.typeform.com"
logger = logging.getLogger(__name__)

def get_typeform_details(form_id, token):
    """Fetch Typeform form structure/details"""
    if not form_id:
        return {"error": "Form ID is required"}

    url = f"{TYPEFORM_API_BASE}/forms/{form_id}"
    headers = {"Authorization": f"Bearer {token.strip()}"}
    print(f"[Typeform] Fetching form details: {url}")

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error fetching Typeform details: {e}")
        return {"error": str(e), "status_code": getattr(e.response, "status_code", None)}
    except Exception as e:
        logger.error(f"Unexpected error fetching Typeform details: {e}")
        return {"error": str(e)}


def fetch_typeform_data(form_id, token):
    """Fetch responses (submissions) from Typeform"""
    if not form_id:
        return {"error": "Form ID is required"}

    url = f"{TYPEFORM_API_BASE}/forms/{form_id}/responses"
    headers = {"Authorization": f"Bearer {token.strip()}"}
    print(f"[Typeform] Fetching responses: {url}")

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error fetching Typeform responses: {e}")
        return {"error": str(e), "status_code": getattr(e.response, "status_code", None)}
    except Exception as e:
        logger.error(f"Unexpected error fetching Typeform responses: {e}")
        return {"error": str(e)}
