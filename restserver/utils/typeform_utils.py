import requests
import logging

TYPEFORM_API_BASE = "https://api.typeform.com"
logger = logging.getLogger(__name__)


def get_typeform_details(form_id, token):
    if not form_id:
        return {"error": "Form ID is required"}

    url = f"{TYPEFORM_API_BASE}/forms/{form_id}"
    headers = {
        "Authorization": f"Bearer {token.strip()}"
    }
    print(f"Header: {headers}")  # ✅ fixed printing

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error while fetching Typeform details: {str(e)}")
        return {
            "error": f"HTTP Error: {str(e)}",
            "status_code": getattr(e.response, "status_code", None),
            "response": response.text
        }
    except Exception as e:
        logger.error(f"Unexpected error while fetching Typeform details: {str(e)}")
        return {"error": str(e)}


def fetch_typeform_data(form_id, token):
    if not form_id:
        return {"error": "Form ID is required"}

    url = f"{TYPEFORM_API_BASE}/forms/{form_id}/responses"
    headers = {
        "Authorization": f"Bearer {token.strip()}"
    }
    print(f"Header: {headers}")  # ✅ fixed printing

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error while fetching Typeform responses: {str(e)}")
        return {
            "error": f"HTTP Error: {str(e)}",
            "status_code": getattr(e.response, "status_code", None),
            "response": response.text
        }
    except Exception as e:
        logger.error(f"Unexpected error while fetching Typeform responses: {str(e)}")
        return {"error": str(e)}
