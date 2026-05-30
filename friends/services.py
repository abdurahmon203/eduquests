from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import FriendRequest, Friendship, Notification

User = get_user_model()


def _normalize_pair(user_a, user_b):
    if user_a.pk <= user_b.pk:
        return user_a, user_b
    return user_b, user_a


def are_friends(user_a, user_b):
    if not user_a or not user_b or user_a.pk == user_b.pk:
        return False
    u1, u2 = _normalize_pair(user_a, user_b)
    return Friendship.objects.filter(user1=u1, user2=u2).exists()


def get_pending_request(from_user, to_user):
    return FriendRequest.objects.filter(
        from_user=from_user,
        to_user=to_user,
        accepted=False,
    ).first()


def has_pending_request_between(user_a, user_b):
    return FriendRequest.objects.filter(
        accepted=False,
    ).filter(
        Q(from_user=user_a, to_user=user_b) | Q(from_user=user_b, to_user=user_a)
    ).exists()


def get_friends_queryset(user):
    friend_ids = set()
    for u1_id, u2_id in Friendship.objects.filter(
        Q(user1=user) | Q(user2=user)
    ).values_list("user1_id", "user2_id"):
        if u1_id == user.pk:
            friend_ids.add(u2_id)
        else:
            friend_ids.add(u1_id)
    return User.objects.filter(pk__in=friend_ids).order_by("username")


def create_notification(recipient, sender, notification_type, message):
    return Notification.objects.create(
        recipient=recipient,
        sender=sender,
        notification_type=notification_type,
        message=message,
    )


def send_friend_request(from_user, to_user):
    if from_user.pk == to_user.pk:
        raise ValueError("You cannot add yourself as a friend.")

    if are_friends(from_user, to_user):
        raise ValueError("You are already friends with this user.")

    if has_pending_request_between(from_user, to_user):
        reverse = get_pending_request(to_user, from_user)
        if reverse:
            return accept_friend_request(reverse, from_user)
        raise ValueError("A friend request is already pending.")

    request = FriendRequest.objects.create(from_user=from_user, to_user=to_user)
    create_notification(
        recipient=to_user,
        sender=from_user,
        notification_type=Notification.FRIEND_REQUEST,
        message=f"@{from_user.username} sent you a friend request.",
    )
    return request


def accept_friend_request(friend_request, acting_user):
    if friend_request.to_user_id != acting_user.pk:
        raise PermissionError("You cannot accept this request.")

    if friend_request.accepted:
        raise ValueError("This request was already accepted.")

    if are_friends(friend_request.from_user, friend_request.to_user):
        friend_request.delete()
        raise ValueError("You are already friends.")

    u1, u2 = _normalize_pair(friend_request.from_user, friend_request.to_user)
    Friendship.objects.get_or_create(user1=u1, user2=u2)

    friend_request.accepted = True
    friend_request.save(update_fields=["accepted"])

    create_notification(
        recipient=friend_request.from_user,
        sender=friend_request.to_user,
        notification_type=Notification.FRIEND_ACCEPTED,
        message=f"@{friend_request.to_user.username} accepted your friend request.",
    )

    FriendRequest.objects.filter(
        accepted=False,
    ).filter(
        Q(from_user=friend_request.from_user, to_user=friend_request.to_user)
        | Q(from_user=friend_request.to_user, to_user=friend_request.from_user)
    ).exclude(pk=friend_request.pk).delete()

    return friend_request


def reject_friend_request(friend_request, acting_user):
    if friend_request.to_user_id != acting_user.pk:
        raise PermissionError("You cannot reject this request.")
    if friend_request.accepted:
        raise ValueError("This request was already accepted.")
    friend_request.delete()


def remove_friendship(user, friend):
    if user.pk == friend.pk:
        raise ValueError("Invalid operation.")

    u1, u2 = _normalize_pair(user, friend)
    Friendship.objects.filter(user1=u1, user2=u2).delete()

    FriendRequest.objects.filter(
        Q(from_user=user, to_user=friend) | Q(from_user=friend, to_user=user)
    ).delete()


def get_relationship_status(viewer, target):
    if viewer.pk == target.pk:
        return "self"
    if are_friends(viewer, target):
        return "friends"
    outgoing = get_pending_request(viewer, target)
    if outgoing:
        return "pending_outgoing"
    incoming = get_pending_request(target, viewer)
    if incoming:
        return "pending_incoming"
    return "none"
