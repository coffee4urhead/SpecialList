"""
ASGI config for JobJab project.
"""

import os

# Set DJANGO_SETTINGS_MODULE *before* anything else
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'JobJab.settings')

# Import and set up Django
import django
django.setup()  # <-- this must happen BEFORE importing routing or models

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import JobJab.chats.routing  # Import AFTER django.setup()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            JobJab.chats.routing.websocket_urlpatterns
        )
    ),
})
