from django.urls import re_path
from .consumers import TypeformRealtimeConsumer

websocket_urlpatterns = [
    re_path(r'ws/$', TypeformRealtimeConsumer.as_asgi()),
]
