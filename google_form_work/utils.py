import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SERVICE_ACCOUNT_FILE = "gxihiring-d7185498ec0f.json"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

def fetch_google_form_responses(sheet_id, range_name='Form Responses 1!A:Z'):
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=sheet_id, range=range_name).execute()
    values = result.get('values', [])

    if not values:
        return []

    headers = values[0]
    responses = []

    for row in values[1:]:
        response_data = {headers[i]: row[i] if i < len(row) else None for i in range(len(headers))}
        responses.append(response_data)

    return responses
