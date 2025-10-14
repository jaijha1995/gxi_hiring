import gspread
from google.oauth2.service_account import Credentials

# Path to your service account key
SERVICE_ACCOUNT_FILE = "gxihiring-d7185498ec0f.json"

# Define scopes
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# Authenticate
creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=SCOPES
)

client = gspread.authorize(creds)

# Google Sheet ID
SHEET_ID = "16irAL1EdtAZm-DBCA-ffy-FM0giEkrDtBNIHxu4Y4r4"

# Open the sheet
sheet = client.open_by_key(SHEET_ID)
worksheet = sheet.sheet1  # First sheet

# Fetch all responses
responses = worksheet.get_all_records()

# Print responses
for response in responses:
    print(response)
