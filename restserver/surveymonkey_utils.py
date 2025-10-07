import requests
from django.conf import settings

SURVEYMONKEY_API_BASE = "https://api.surveymonkey.com/v3"


def get_survey_details(survey_id):
    """
    Get SurveyMonkey survey details.
    """
    headers = {
        "Authorization": f"Bearer {settings.SURVEYMONKEY_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    url = f"{SURVEYMONKEY_API_BASE}/surveys/{survey_id}/details"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def fetch_survey_data(survey_id):
    """
    Get SurveyMonkey survey responses.
    """
    headers = {
        "Authorization": f"Bearer {settings.SURVEYMONKEY_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    url = f"{SURVEYMONKEY_API_BASE}/surveys/{survey_id}/responses/bulk"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()
