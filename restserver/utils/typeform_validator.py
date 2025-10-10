import re
from datetime import datetime

def is_valid_email(email):
    """Check if email format is valid."""
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))

def is_valid_phone(phone):
    """Check if phone number is valid."""
    return bool(re.match(r"^\+?\d{7,15}$", phone))

def is_valid_date(date_str):
    """Check if date string is valid ISO date."""
    try:
        datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return True
    except Exception:
        return False

def filter_correct_answers(answers):
    """
    Filters answers to ensure only correct data according to type.
    Returns a cleaned list.
    """
    correct_answers = []
    for ans in answers:
        type_ = ans.get("type")
        if type_ == "text" and ans.get("text"):
            correct_answers.append({"type": "text", "text": ans["text"]})
        elif type_ == "email" and is_valid_email(ans.get("email", "")):
            correct_answers.append({"type": "email", "email": ans["email"]})
        elif type_ == "phone_number" and is_valid_phone(ans.get("phone_number", "")):
            correct_answers.append({"type": "phone_number", "phone_number": ans["phone_number"]})
        elif type_ == "boolean" and isinstance(ans.get("boolean"), bool):
            correct_answers.append({"type": "boolean", "boolean": ans["boolean"]})
        elif type_ == "date" and is_valid_date(ans.get("date", "")):
            correct_answers.append({"type": "date", "date": ans["date"]})
        elif type_ == "number" and isinstance(ans.get("number"), (int, float)):
            correct_answers.append({"type": "number", "number": ans["number"]})
        elif type_ == "choice" and isinstance(ans.get("choice"), dict) and ans["choice"].get("id"):
            correct_answers.append({"type": "choice", "choice": ans["choice"]})
        elif type_ == "choices" and isinstance(ans.get("choices"), dict) and ans["choices"].get("ids"):
            correct_answers.append({"type": "choices", "choices": ans["choices"]})
    return correct_answers