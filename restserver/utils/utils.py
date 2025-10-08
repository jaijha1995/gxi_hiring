from django.db import models
from django.utils import timezone

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger



class TimestampMixin(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


def paginate_queryset(queryset, request):
    page = request.query_params.get("page", 1)
    page_size = request.query_params.get("page_size", 10)
    try:
        page = int(page)
        page_size = int(page_size)
    except ValueError:
        page = 1
        page_size = 10

    paginator = Paginator(queryset, page_size)
    try:
        objects = paginator.page(page)
    except PageNotAnInteger:
        objects = paginator.page(1)
    except EmptyPage:
        objects = []

    pagination_data = {
        "total": paginator.count,
        "page": page,
        "page_size": page_size,
        "total_pages": paginator.num_pages,
        "has_next": objects.has_next() if objects else False,
        "has_previous": objects.has_previous() if objects else False,
    }
    return objects, pagination_data



import random
import smtplib
from email.mime.text import MIMEText
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import requests

def generate_otp():
    return str(random.randint(1000, 9999))

def send_otp_email(email, otp):
    subject = 'Your OTP'
    message = f'Your OTP is: {otp}'

    from_email = 'jai@skylabstech.com'

    email_message = EmailMessage(subject, message, from_email, [email])
    email_message.send()



def send_welcome_email(self, email):
        subject = 'Welcome to YourApp!'
        html_message = render_to_string('welcome_email_template.html', {'email': email})
        plain_message = strip_tags(html_message)
        from_email = 'jai@skylabstech.com'  # Replace with your email
        recipient_list = [email]

        email = EmailMessage(subject, plain_message, from_email, recipient_list)
        email.content_subtype = "html"
        email.send()



import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from django.conf import settings

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

def get_sheet_names(spreadsheet_id):
    creds = service_account.Credentials.from_service_account_file(
        settings.GOOGLE_SHEETS_CREDENTIALS_FILE, scopes=SCOPES
    )
    service = build("sheets", "v4", credentials=creds)
    sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheet_titles = [sheet['properties']['title'] for sheet in sheet_metadata.get('sheets', [])]
    return sheet_titles


def fetch_sheet_data(spreadsheet_id, sheet_name=None, range_cols="A:Z"):
    creds = service_account.Credentials.from_service_account_file(
        settings.GOOGLE_SHEETS_CREDENTIALS_FILE, scopes=SCOPES
    )
    service = build("sheets", "v4", credentials=creds)

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
    return values
