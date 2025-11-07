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


# utils.py
import io
from xhtml2pdf import pisa
from django.core.files.base import ContentFile


def generate_reference_style_cv(submission_data):
    """Generate a professional PDF CV styled like the reference Shivam Singh resume."""

    name = submission_data.get("Name", "Candidate").title()
    role = submission_data.get("Role_Type", "Professional")
    email = submission_data.get("Email", "")
    phone = submission_data.get("Phone", "")
    location = submission_data.get("Location", "")
    state = submission_data.get("State", "")
    country = submission_data.get("Country", "")
    summary = submission_data.get("Summary", "")
    langs = submission_data.get("Languages Known", [])
    tech_exp = submission_data.get("Tech_Experience", {})
    prof_exp = submission_data.get("Professional_Experience", [])
    education = submission_data.get("Education_History", [])
    certs = submission_data.get("Certifications", [])

    # Helper function for safe joining
    def join_list(items):
        return ", ".join(items) if isinstance(items, list) else str(items)

    # Dynamic skills extraction from Tech_Experience
    skill_set = []
    for role_key, details in tech_exp.items():
        if isinstance(details, dict):
            for skill in details.keys():
                if isinstance(details[skill], (dict, list)):
                    skill_set.append(skill)
                elif isinstance(details[skill], str):
                    skill_set.append(f"{skill}: {details[skill]}")

    # ---------------------- HTML TEMPLATE ----------------------
    html = f"""
    <html>
    <head>
        <style>
            @page {{
                size: A4;
                margin: 0;
            }}
            body {{
                font-family: 'Helvetica', sans-serif;
                margin: 0;
                padding: 0;
                color: #222;
            }}
            .page {{
                display: flex;
                flex-direction: row;
                width: 100%;
                min-height: 100vh;
            }}
            .sidebar {{
                background-color: #003366;
                color: white;
                width: 32%;
                padding: 25px;
            }}
            .sidebar h1 {{
                font-size: 22px;
                margin-bottom: 5px;
                line-height: 1.2;
            }}
            .sidebar h3 {{
                font-size: 12px;
                color: #9ec7ff;
                margin-top: 0;
            }}
            .sidebar h2 {{
                border-bottom: 1px solid #9ec7ff;
                padding-bottom: 4px;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-top: 20px;
            }}
            .sidebar p {{
                font-size: 11px;
                line-height: 1.4;
                margin: 4px 0;
            }}
            .sidebar ul {{
                list-style-type: none;
                padding-left: 10px;
                margin: 4px 0;
            }}
            .sidebar ul li {{
                font-size: 11px;
                margin-bottom: 3px;
            }}
            .main {{
                background-color: white;
                width: 68%;
                padding: 30px;
                box-sizing: border-box;
            }}
            .section {{
                margin-bottom: 18px;
            }}
            .section h2 {{
                color: #003366;
                border-bottom: 2px solid #003366;
                font-size: 13px;
                margin-bottom: 6px;
                text-transform: uppercase;
            }}
            .section h3 {{
                margin-bottom: 3px;
                font-size: 12px;
                color: #111;
            }}
            .section p {{
                font-size: 11px;
                margin: 2px 0;
                line-height: 1.5;
            }}
            .bullet {{
                margin-left: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="page">
            <!-- LEFT SIDEBAR -->
            <div class="sidebar">
                <h1>{name}</h1>
                <h3>{role}</h3>

                <h2>Contact</h2>
                <p>{email}</p>
                <p>{phone}</p>
                <p>{location}, {state}, {country}</p>

                {"<h2>Languages</h2><ul>" + ''.join(f"<li>{lang}</li>" for lang in langs) + "</ul>" if langs else ""}

                {"<h2>Skills</h2><ul>" + ''.join(f"<li>{skill}</li>" for skill in skill_set) + "</ul>" if skill_set else ""}
            </div>

            <!-- RIGHT MAIN -->
            <div class="main">
                <div class="section">
                    <h2>Summary</h2>
                    <p>{summary or 'Experienced professional skilled in business analysis and technical integration.'}</p>
                </div>

                {"<div class='section'><h2>Experience</h2>" + ''.join([
                    f"<h3>{exp.get('Role','')} - {exp.get('Organisation','')}</h3>"
                    f"<p><i>{exp.get('Start_Date','')} to {exp.get('End_Date','')} | {exp.get('Location','')}</i></p>"
                    f"<p>CTC: {exp.get('CTC_INR','')} LPA</p>"
                    f"{'<p class=bullet>'+exp.get('Responsibilities','')+'</p>' if exp.get('Responsibilities') else ''}"
                    for exp in prof_exp
                ]) + '</div>' if prof_exp else ''}

                {"<div class='section'><h2>Education</h2>" + ''.join([
                    f"<p><b>{edu.get('Qualification','')}</b> — {edu.get('University','')} ({edu.get('Start_Date','')} - {edu.get('End_Date','')})<br/>"
                    f"Specialisation: {edu.get('Specialisation','')} | Score: {edu.get('Score','')}</p>"
                    for edu in education
                ]) + '</div>' if education else ''}

                {"<div class='section'><h2>Certifications</h2><ul>" + ''.join(f"<li>{c}</li>" for c in certs) + "</ul></div>" if certs else ""}
            </div>
        </div>
    </body>
    </html>
    """

    # Convert HTML → PDF
    pdf_buffer = io.BytesIO()
    pisa.CreatePDF(html, dest=pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()
