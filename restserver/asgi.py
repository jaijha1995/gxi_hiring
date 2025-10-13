import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "restserver.settings")
django.setup()

import google_sheet.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # normal HTTP requests
    "websocket": AuthMiddlewareStack(  # WebSocket requests
        URLRouter(
            google_sheet.routing.websocket_urlpatterns
        )
    ),
})
