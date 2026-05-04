import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from urllib.parse import parse_qs


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for user-specific notifications.
    Each authenticated user joins their own group: 'notifications_<user_id>'
    """

    async def connect(self):
        # Get user from scope (set by AuthMiddlewareStack or token middleware)
        self.user = self.scope.get("user", None)
        
        # Try token-based auth from query string
        if not self.user or self.user.is_anonymous:
            token = parse_qs(self.scope.get("query_string", b"").decode()).get("token", [None])[0]
            if token:
                self.user = await self.get_user_from_token(token)
        
        if not self.user or self.user.is_anonymous:
            await self.close()
            return

        self.group_name = f"notifications_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_notification(self, event):
        """Handle notification events pushed from the backend."""
        await self.send(text_data=json.dumps(event["data"]))

    @database_sync_to_async
    def get_user_from_token(self, token):
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            from django.contrib.auth import get_user_model
            User = get_user_model()
            access_token = AccessToken(token)
            return User.objects.get(id=access_token["user_id"])
        except Exception:
            return None


class CourseConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for course-specific real-time events.
    All users viewing a course join the group: 'course_<course_id>'
    Events: new_question, new_answer, new_review, new_announcement
    """

    async def connect(self):
        self.course_id = self.scope["url_route"]["kwargs"]["course_id"]
        self.group_name = f"course_{self.course_id}"

        # Try token-based auth
        self.user = self.scope.get("user", None)
        if not self.user or self.user.is_anonymous:
            token = parse_qs(self.scope.get("query_string", b"").decode()).get("token", [None])[0]
            if token:
                self.user = await self.get_user_from_token(token)

        if not self.user or self.user.is_anonymous:
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Event handlers - called when channel_layer.group_send() is used
    async def course_event(self, event):
        """Handle any course event (question, answer, review, announcement)."""
        await self.send(text_data=json.dumps(event["data"]))

    @database_sync_to_async
    def get_user_from_token(self, token):
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            from django.contrib.auth import get_user_model
            User = get_user_model()
            access_token = AccessToken(token)
            return User.objects.get(id=access_token["user_id"])
        except Exception:
            return None
