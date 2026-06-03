from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from .models import ChatMessage, ChatReadState, ChatRoom, UserPresence
from .services import _normalize_pair, are_friends

User = get_user_model()


def get_or_create_room(user_a, user_b):
    if not are_friends(user_a, user_b):
        raise PermissionError("You can only chat with friends.")
    u1, u2 = _normalize_pair(user_a, user_b)
    room, _created = ChatRoom.objects.get_or_create(user1=u1, user2=u2)
    return room


def user_can_access_room(user, room):
    return room.involves_user(user) and are_friends(room.user1, room.user2)


def get_read_state(room, user):
    state, _ = ChatReadState.objects.get_or_create(room=room, user=user)
    return state


def mark_room_read(room, user):
    state = get_read_state(room, user)
    state.last_read_at = timezone.now()
    state.save(update_fields=["last_read_at"])
    return state


def unread_count_for_room(room, user):
    state = ChatReadState.objects.filter(room=room, user=user).first()
    since = state.last_read_at if state else None
    qs = ChatMessage.objects.filter(room=room, is_deleted=False).exclude(sender=user)
    if since:
        qs = qs.filter(created_at__gt=since)
    return qs.count()


def unread_counts_by_friend_ids(user):
    """Returns dict {friend_user_id: unread_count}."""
    rooms = ChatRoom.objects.filter(Q(user1=user) | Q(user2=user))
    result = {}
    for room in rooms:
        friend = room.other_user(user)
        result[friend.pk] = unread_count_for_room(room, user)
    return result


def total_unread_chat_count(user):
    return sum(unread_counts_by_friend_ids(user).values())


def serialize_message(msg, viewer=None):
    sender = msg.sender
    data = {
        "id": msg.pk,
        "room_id": msg.room_id,
        "sender_id": sender.pk,
        "sender_username": sender.username,
        "content": "" if msg.is_deleted else msg.content,
        "created_at": msg.created_at.isoformat(),
        "updated_at": msg.updated_at.isoformat(),
        "is_edited": msg.is_edited,
        "is_deleted": msg.is_deleted,
        "is_mine": viewer.pk == sender.pk if viewer else False,
    }
    return data


def get_room_messages(room, limit=200):
    msgs = (
        ChatMessage.objects.filter(room=room)
        .select_related("sender")
        .order_by("created_at")[:limit]
    )
    return list(msgs)


def create_message(room, sender, content):
    content = (content or "").strip()
    if not content:
        raise ValueError("Message cannot be empty.")
    if len(content) > 4000:
        raise ValueError("Message is too long.")
    return ChatMessage.objects.create(room=room, sender=sender, content=content)


def soft_delete_message(message, user):
    if message.sender_id != user.pk:
        raise PermissionError("You can only delete your own messages.")
    message.is_deleted = True
    message.content = ""
    message.save(update_fields=["is_deleted", "content", "updated_at"])
    return message


def edit_message(message, user, new_content):
    if message.sender_id != user.pk:
        raise PermissionError("You can only edit your own messages.")
    if message.is_deleted:
        raise ValueError("Cannot edit a deleted message.")
    new_content = (new_content or "").strip()
    if not new_content:
        raise ValueError("Message cannot be empty.")
    message.content = new_content
    message.is_edited = True
    message.save(update_fields=["content", "is_edited", "updated_at"])
    return message


def search_messages(room, user, query, limit=50):
    if not user_can_access_room(user, room):
        raise PermissionError("Access denied.")
    q = (query or "").strip()
    if not q:
        return []
    return list(
        ChatMessage.objects.filter(
            room=room,
            is_deleted=False,
            content__icontains=q,
        )
        .select_related("sender")
        .order_by("-created_at")[:limit]
    )


def set_user_online(user, online=True):
    presence, _ = UserPresence.objects.get_or_create(user=user)
    presence.is_online = online
    presence.last_seen = timezone.now()
    presence.save(update_fields=["is_online", "last_seen"])
    return presence


def get_presence(user):
    presence, _ = UserPresence.objects.get_or_create(user=user)
    return presence


def serialize_presence(presence):
    return {
        "user_id": presence.user_id,
        "is_online": presence.is_online,
        "last_seen": presence.last_seen.isoformat(),
    }
