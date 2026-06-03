import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone

from .chat_services import (
    create_message,
    get_presence,
    mark_room_read,
    serialize_message,
    serialize_presence,
    set_user_online,
    user_can_access_room,
)
from .models import ChatRoom


class ChatConsumer(AsyncJsonWebsocketConsumer):
    room_id = None
    room_group = None

    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        self.room_id = int(self.scope["url_route"]["kwargs"]["room_id"])
        room = await self._get_room(self.room_id)
        if not room or not await self._can_access(room):
            await self.close()
            return

        self.room_group = f"chat_room_{self.room_id}"
        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

        await self._set_online(True)
        presence = await self._get_presence(self.user)
        await self.channel_layer.group_send(
            self.room_group,
            {
                "type": "chat.presence",
                "payload": serialize_presence(presence),
            },
        )

    async def disconnect(self, close_code):
        if self.room_group:
            await self.channel_layer.group_discard(self.room_group, self.channel_name)
        if getattr(self, "user", None) and self.user.is_authenticated:
            await self._set_online(False)
            if self.room_group:
                presence = await self._get_presence(self.user)
                await self.channel_layer.group_send(
                    self.room_group,
                    {
                        "type": "chat.presence",
                        "payload": serialize_presence(presence),
                    },
                )

    async def receive_json(self, content, **kwargs):
        if not self.user.is_authenticated:
            return

        msg_type = content.get("type")

        if msg_type == "chat.message":
            text = content.get("content", "")
            try:
                message = await self._create_message(text)
                payload = await self._serialize(message)
                await self.channel_layer.group_send(
                    self.room_group,
                    {"type": "chat.message", "payload": payload},
                )
            except (ValueError, PermissionError) as exc:
                await self.send_json({"type": "chat.error", "error": str(exc)})

        elif msg_type == "chat.typing":
            is_typing = bool(content.get("is_typing", False))
            await self.channel_layer.group_send(
                self.room_group,
                {
                    "type": "chat.typing",
                    "payload": {
                        "user_id": self.user.pk,
                        "username": self.user.username,
                        "is_typing": is_typing,
                    },
                },
            )

        elif msg_type == "chat.read":
            state = await self._mark_read()
            await self.channel_layer.group_send(
                self.room_group,
                {
                    "type": "chat.read",
                    "payload": {
                        "user_id": self.user.pk,
                        "last_read_at": state.last_read_at.isoformat(),
                    },
                },
            )

    async def chat_message(self, event):
        await self.send_json({"type": "chat.message", "message": event["payload"]})

    async def chat_typing(self, event):
        payload = event["payload"]
        if payload.get("user_id") == self.user.pk:
            return
        await self.send_json({"type": "chat.typing", **payload})

    async def chat_read(self, event):
        await self.send_json({"type": "chat.read", **event["payload"]})

    async def chat_presence(self, event):
        payload = event["payload"]
        if payload.get("user_id") == self.user.pk:
            return
        await self.send_json({"type": "chat.presence", **payload})

    async def chat_message_update(self, event):
        await self.send_json({"type": "chat.message_update", "message": event["payload"]})

    @database_sync_to_async
    def _get_room(self, room_id):
        try:
            return ChatRoom.objects.select_related("user1", "user2").get(pk=room_id)
        except ChatRoom.DoesNotExist:
            return None

    @database_sync_to_async
    def _can_access(self, room):
        return user_can_access_room(self.user, room)

    @database_sync_to_async
    def _create_message(self, text):
        room = ChatRoom.objects.get(pk=self.room_id)
        return create_message(room, self.user, text)

    @database_sync_to_async
    def _serialize(self, message):
        return serialize_message(message, self.user)

    @database_sync_to_async
    def _mark_read(self):
        room = ChatRoom.objects.get(pk=self.room_id)
        return mark_room_read(room, self.user)

    @database_sync_to_async
    def _set_online(self, online):
        set_user_online(self.user, online)

    @database_sync_to_async
    def _get_presence(self, user):
        return get_presence(user)

