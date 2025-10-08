import requests
import json

# Typeform API URL
url = "https://api.typeform.com/forms/iBGYbV3s/responses"

# Authorization header
headers = {
    "Authorization": "Bearer fsfhsfgf"
}

try:
    # Fetch data
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise error if request fails
    data = response.json()

    # Save data to a JSON file
    with open("typeform_responses.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print("Data saved successfully to typeform_responses.json")

except requests.exceptions.HTTPError as errh:
    print(f"HTTP Error: {errh}")
except requests.exceptions.ConnectionError as errc:
    print(f"Connection Error: {errc}")
except requests.exceptions.Timeout as errt:
    print(f"Timeout Error: {errt}")
except requests.exceptions.RequestException as err:
    print(f"Error: {err}")
