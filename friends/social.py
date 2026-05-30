from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from gamification.models import UserProgress
from gamification.xp import build_user_stats, get_user_streak

from .models import FriendRequest
from .services import get_friends_queryset

User = get_user_model()


def get_friend_rank(user):
    friends = list(get_friends_queryset(user))
    participants = friends + [user]
    ranked = sorted(
        participants,
        key=lambda u: (-build_user_stats(u)["total_xp"], u.username),
    )
    for rank, participant in enumerate(ranked, start=1):
        if participant.pk == user.pk:
            return rank, len(ranked)
    return 1, max(1, len(ranked))


def get_social_hub_stats(user):
    friends_count = get_friends_queryset(user).count()
    pending_requests = FriendRequest.objects.filter(
        to_user=user,
        accepted=False,
    ).count()
    rank, squad_size = get_friend_rank(user)

    friend_ids = list(get_friends_queryset(user).values_list("pk", flat=True))
    activity = 0
    week_ago = timezone.now() - timedelta(days=7)
    for fid in friend_ids:
        friend = User.objects.filter(pk=fid).first()
        if not friend:
            continue
        if get_user_streak(friend) > 0:
            activity += 1
        elif UserProgress.objects.filter(user_id=fid, updated_at__gte=week_ago).exists():
            activity += 1

    return {
        "friends_count": friends_count,
        "pending_requests": pending_requests,
        "friend_rank": rank,
        "squad_size": squad_size,
        "friend_activity": activity,
    }
