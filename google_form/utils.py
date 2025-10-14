# utils.py
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from django.conf import settings

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

def get_sheet_names(spreadsheet_id):
    """Return list of sheet names in a spreadsheet"""
    creds = service_account.Credentials.from_service_account_file(
        settings.GOOGLE_SHEETS_CREDENTIALS_FILE, scopes=SCOPES
    )
    service = build("sheets", "v4", credentials=creds)
    sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheet_titles = [sheet['properties']['title'] for sheet in sheet_metadata.get('sheets', [])]
    return sheet_titles


def fetch_sheet_data(spreadsheet_id, sheet_name=None, range_cols="A:Z"):
    """
    Fetch all data from a Google Sheet tab
    Returns a list of dicts (first row as headers)
    """
    creds = service_account.Credentials.from_service_account_file(
        settings.GOOGLE_SHEETS_CREDENTIALS_FILE, scopes=SCOPES
    )
    service = build("sheets", "v4", credentials=creds)

    # Get sheet name if not provided
    if not sheet_name:
        sheet_names = get_sheet_names(spreadsheet_id)
        if not sheet_names:
            raise Exception("No sheet tabs found in this spreadsheet")
        sheet_name = sheet_names[0]  # Default to first sheet

    range_name = f"{sheet_name}!{range_cols}"
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=range_name
    ).execute()
    values = result.get("values", [])

    if not values:
        return []

    headers = values[0]
    data = []
    for row in values[1:]:
        # Fill missing columns with None
        row_data = {headers[i]: row[i] if i < len(row) else None for i in range(len(headers))}
        data.append(row_data)
    return data
