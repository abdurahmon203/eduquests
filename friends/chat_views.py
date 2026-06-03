import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from .chat_services import (
    edit_message,
    get_or_create_room,
    get_presence,
    get_room_messages,
    mark_room_read,
    search_messages,
    serialize_message,
    serialize_presence,
    soft_delete_message,
    unread_count_for_room,
    user_can_access_room,
)
from .models import ChatMessage, ChatRoom
from .services import are_friends
from .social import get_social_hub_stats

User = get_user_model()


def _broadcast(room_id, event_type, payload):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    async_to_sync(channel_layer.group_send)(
        f"chat_room_{room_id}",
        {"type": event_type, "payload": payload},
    )


@login_required
def chat_with_friend(request, user_id):
    friend = get_object_or_404(User, pk=user_id, is_active=True)
    if friend.pk == request.user.pk:
        return redirect("friends_list")
    if not are_friends(request.user, friend):
        return redirect("friends_list")

    try:
        room = get_or_create_room(request.user, friend)
    except PermissionError:
        return redirect("friends_list")

    mark_room_read(room, request.user)
    messages = get_room_messages(room)
    message_list = [
        serialize_message(m, request.user) for m in messages
    ]
    friend_presence = serialize_presence(get_presence(friend))

    return render(
        request,
        "friends/chat.html",
        {
            "room": room,
            "friend": friend,
            "messages_json": json.dumps(message_list),
            "friend_presence": friend_presence,
            "hub_stats": get_social_hub_stats(request.user),
        },
    )


@login_required
@require_POST
def chat_delete_message(request, message_id):
    message = get_object_or_404(
        ChatMessage.objects.select_related("room", "sender"),
        pk=message_id,
    )
    if not user_can_access_room(request.user, message.room):
        return JsonResponse({"error": "Forbidden"}, status=403)
    try:
        soft_delete_message(message, request.user)
    except PermissionError as exc:
        return JsonResponse({"error": str(exc)}, status=403)
    payload = serialize_message(message, request.user)
    _broadcast(message.room_id, "chat.message_update", payload)
    return JsonResponse({"ok": True, "message": payload})


@login_required
@require_POST
def chat_edit_message(request, message_id):
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    message = get_object_or_404(
        ChatMessage.objects.select_related("room", "sender"),
        pk=message_id,
    )
    if not user_can_access_room(request.user, message.room):
        return JsonResponse({"error": "Forbidden"}, status=403)
    try:
        edit_message(message, request.user, body.get("content", ""))
    except (PermissionError, ValueError) as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    payload = serialize_message(message, request.user)
    _broadcast(message.room_id, "chat.message_update", payload)
    return JsonResponse({"ok": True, "message": payload})


@login_required
@require_GET
def chat_search(request, room_id):
    room = get_object_or_404(ChatRoom, pk=room_id)
    if not user_can_access_room(request.user, room):
        return JsonResponse({"error": "Forbidden"}, status=403)
    q = request.GET.get("q", "")
    results = search_messages(room, request.user, q)
    return JsonResponse(
        {
            "results": [
                serialize_message(m, request.user) for m in results
            ]
        }
    )


@login_required
@require_GET
def chat_unread_count(request, user_id):
    friend = get_object_or_404(User, pk=user_id)
    if not are_friends(request.user, friend):
        return JsonResponse({"count": 0})
    try:
        room = get_or_create_room(request.user, friend)
    except PermissionError:
        return JsonResponse({"count": 0})
    return JsonResponse({"count": unread_count_for_room(room, request.user)})
