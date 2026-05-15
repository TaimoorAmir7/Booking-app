import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken

from api.models import ChatSession, User
from api.services.chat import process_chat_message

logger = logging.getLogger("api.ws")


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.user = await self._authenticate()
        if not self.user or not getattr(self.user, "is_authenticated", False):
            await self.close(code=4401)
            return

        self.session = await self._get_session()
        if not self.session:
            await self.close(code=4404)
            return

        self.group_name = f"chat_{self.session_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json(
            {
                "type": "connected",
                "session_id": self.session_id,
                "messages": self.session.messages,
            }
        )

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        message = (content.get("content") or "").strip()
        if not message:
            await self.send_json({"type": "error", "error": "Empty message"})
            return

        confirm = bool(content.get("confirm_booking", False))
        result = await process_chat_message(
            self.session, self.user, message, confirm_booking=confirm
        )
        await self.channel_layer.group_send(
            self.group_name,
            {"type": "chat.broadcast", "payload": result},
        )

    async def chat_broadcast(self, event):
        await self.send_json({"type": "chat.message", **event["payload"]})

    @database_sync_to_async
    def _authenticate(self):
        query = self.scope.get("query_string", b"").decode()
        token = None
        for part in query.split("&"):
            if part.startswith("token="):
                token = part.split("=", 1)[1]
                break
        headers = dict(self.scope.get("headers", []))
        auth = headers.get(b"authorization", b"").decode()
        if auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1].strip()
        if not token:
            return None
        try:
            access = AccessToken(token)
            return User.objects.get(pk=access["user_id"])
        except Exception:
            logger.warning("[ws] invalid token")
            return None

    @database_sync_to_async
    def _get_session(self):
        try:
            return ChatSession.objects.get(id=self.session_id, user_id=self.user.pk)
        except ChatSession.DoesNotExist:
            return None
