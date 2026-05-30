from .models import FriendRequest, Notification


def friends_context(request):
    if not request.user.is_authenticated:
        return {
            "pending_friend_requests_count": 0,
            "unread_notifications_count": 0,
        }

    return {
        "pending_friend_requests_count": FriendRequest.objects.filter(
            to_user=request.user,
            accepted=False,
        ).count(),
        "unread_notifications_count": Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).count(),
    }
