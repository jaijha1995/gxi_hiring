import asyncio
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils.dateparse import parse_datetime
from .models import TypeformAnswer, Hiring_process
from .utils.typeform_utils import fetch_typeform_data

logger = logging.getLogger(__name__)

# FIELD_NAME_MAP from your code
FIELD_NAME_MAP = {
    "first_name": ["GSdr0vI52V2H", "xrMAlvBbMrM9", "C66jIidCS4KW"],
    "last_name": ["K4rp3rvgL1jg", "jsHa09RwZXcj", "8WFGWnAiQbdf"],
    "phone_number": ["skkeXrAQqfxg", "XBcEyKAmDBCK", "vTNQ6dnhA1t"],
    "email": ["PljYRNxTMKTb", "or3Akhg0oKlf", "WFvWBoE3fXey"],
    "country": ["hfVE1X2KrFdp", "BcmMmw15AJLz", "9RJE2mqcqlBH"],
    "language": ["eS4GL5ioI4bR", "41qUwfksG32C", "AhyIy57Nai1H"],
    "JOb_Resposiltes": ["JixBI29gKECC", "lBoTQOD9jtqi", "p2KSFFXGM50P"],
    "Company": ["bZmXYzNyRAar", "qosM9BaQgRiz", "9FgFAzwB9SZT"],
    "Experience": ["ifsjUpya0xNx", "UbICuFB7QLwg", "h9YbJLKgnvz9"],
    "Notice_Period": ["QDVKrprS7Vah"],  # IGNORE
    "Joining_date": ["3jaqKHZpq9S6"],  # IGNORE
    "Higest_degree": ["3hxg9RZ07fY7"],  # IGNORE
    "Specialization": ["6g6DKtlVy9sc"],  # IGNORE
    "University": ["xngwRnnQQfMs"],
    "Percentage": ["TGTO7FjaEGRf"],
    "python": ["GaNy7pqrsc8t"],
    "python_rate": ["XsUaFdm29tiW"],
    "RDBMS": ["TOGLRSygikj7"],
    "RDBMS_rate": ["BEvfgv95crJY"],
    "Machine Learning": ["Btbfn7tEo2De"],
    "Machine Learning_rate": ["1LNTgu0cJQ4z"],
    "R_language": ["0z8VIV2t8WXX"],
    "R_language_rate": ["H5ZK7SUO53Uq"],
    "RAVE_developer": ["uyZTlo34AZgh"],
    "RAVE_developer_rate": ["iS2RHphvJ14b"],
    "Cucumber": ["CQ4ijUoGTyQM"],
    "Cucumber_rate": ["Mj5nHG6jhES4"],
    "BDD": ["yFsTMFNUPrkm"],
    "BDD_rate": ["nvyx6BuB41Ls"],
    "Linear Programming": ["GtJyOWE18ugq"],
    "Linear Programming_rate": ["lrLM95WWijzt"],
    "Statistics_and_Probability": ["gGj2wCnIbgUd"],
    "Statistics_and_Probability_rate": ["iW4A9tqh0V5M"],
    "Discrete Mathematics": ["F6CGB3UfonWh"],
    "Discrete Mathematics_rate": ["X1b0Y5y3KX8D"],
}

def map_answers(answers):
    transformed_answers = []
    for ans in answers:
        field_id = ans.get("field", {}).get("id")
        mapped_name = None
        for key, ids in FIELD_NAME_MAP.items():
            if field_id in ids:
                mapped_name = key
                break

        if mapped_name:
            if ans.get("type") == "text":
                transformed_answers.append({mapped_name: ans.get("text")})
            elif ans.get("type") == "phone_number":
                transformed_answers.append({mapped_name: ans.get("phone_number")})
            elif ans.get("type") == "email":
                transformed_answers.append({mapped_name: ans.get("email")})
            elif ans.get("type") == "choices":
                transformed_answers.append({mapped_name: ans.get("choices", {}).get("labels", [])})
            elif ans.get("type") == "choice":
                transformed_answers.append({mapped_name: ans.get("choice", {}).get("label")})
            elif ans.get("type") == "boolean":
                transformed_answers.append({mapped_name: ans.get("boolean")})
            elif ans.get("type") == "date":
                transformed_answers.append({mapped_name: ans.get("date")})
            elif ans.get("type") == "number":
                transformed_answers.append({mapped_name: ans.get("number")})
        else:
            transformed_answers.append(ans)
    return transformed_answers


class TypeformRealtimeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({"message": "Connected to Typeform real-time fetch."}))
        self.fetch_task = asyncio.create_task(self.fetch_loop())

    async def disconnect(self, code):
        if hasattr(self, 'fetch_task'):
            self.fetch_task.cancel()
        logger.info(f"WebSocket disconnected with code: {code}")

    async def fetch_loop(self):
        while True:
            try:
                integrations = await sync_to_async(list)(
                    Hiring_process.objects.filter(integration_type="typeform", token__isnull=False)
                )

                combined_data = []
                total_new = 0
                total_count_all = 0  # total responses across all integrations

                for integration in integrations:
                    responses = await sync_to_async(fetch_typeform_data)(
                        integration.identifier, integration.token
                    )

                    if "error" in responses:
                        combined_data.append({
                            "integration": integration.identifier,
                            "error": responses["error"]
                        })
                        continue

                    sorted_items = sorted(
                        responses.get("items", []),
                        key=lambda x: x.get("submitted_at") or "",
                        reverse=True
                    )

                    integration_responses = []
                    new_count = 0

                    for item in sorted_items:
                        response_id = item.get("response_id")
                        answers = map_answers(item.get("answers", []))
                        landed_at = parse_datetime(item.get("landed_at")) if item.get("landed_at") else None
                        submitted_at = parse_datetime(item.get("submitted_at")) if item.get("submitted_at") else None

                        exists = await sync_to_async(TypeformAnswer.objects.filter(response_id=response_id).exists)()
                        if not exists:
                            await sync_to_async(TypeformAnswer.objects.create)(
                                integration=integration,
                                response_id=response_id,
                                answers=answers,
                                landed_at=landed_at,
                                submitted_at=submitted_at
                            )
                            new_count += 1
                            total_new += 1

                        integration_responses.append({
                            "response_id": response_id,
                            "answers": answers,
                            "landed_at": landed_at.isoformat() if landed_at else None,
                            "submitted_at": submitted_at.isoformat() if submitted_at else None,
                            "is_new": not exists
                        })

                    combined_data.append({
                        "integration": integration.identifier,
                        "responses": integration_responses,
                        "new_count": new_count,
                        "total_count": len(integration_responses)
                    })

                    total_count_all += len(integration_responses)

                # Send combined data for all integrations in one message
                await self.send(
                    text_data=json.dumps({
                        "message": "Typeform responses update",
                        "total_new_responses": total_new,
                        "total_count_all": total_count_all,  # Total responses across all integrations
                        "data": combined_data
                    })
                )

                await asyncio.sleep(5)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in fetch_loop: {e}")
                await self.send(text_data=json.dumps({"error": str(e)}))
                await asyncio.sleep(5)
