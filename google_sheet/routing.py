from django.urls import re_path
from .consumers import TypeformRealtimeConsumer
from google_form_work.consumers import GoogleFormAllSheetsConsumer


websocket_urlpatterns = [
    re_path(r'ws/$', TypeformRealtimeConsumer.as_asgi()),
    re_path(r"ws/forms/$", GoogleFormAllSheetsConsumer.as_asgi())
]
