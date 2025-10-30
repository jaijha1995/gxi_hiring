import requests
from django.conf import settings
from datetime import datetime

def get_ms_access_token():
    if settings.MS_GRAPH_ACCESS_TOKEN:
        return settings.MS_GRAPH_ACCESS_TOKEN

    url = settings.MS_TOKEN_URL
    data = {
        'client_id': settings.MS_CLIENT_ID,
        'scope': settings.MS_GRAPH_SCOPE,
        'client_secret': settings.MS_CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }

    response = requests.post(url, data=data)
    response.raise_for_status()
    token_data = response.json()
    access_token = token_data.get('access_token')
    settings.MS_GRAPH_ACCESS_TOKEN = access_token
    return access_token


def create_teams_meeting(subject, start_time, end_time, organizer_email):
    """
    Creates a Microsoft Teams online meeting.
    """
    access_token = get_ms_access_token()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "subject": subject,
        "startDateTime": start_time,
        "endDateTime": end_time,
        "participants": {
            "organizer": {
                "emailAddress": {"address": organizer_email}
            }
        }
    }

    response = requests.post(
        f"{settings.MS_GRAPH_API_URL}/users/{organizer_email}/onlineMeetings",
        headers=headers,
        json=payload
    )

    response.raise_for_status()
    return response.json()
