from django.db.models import Count, F, IntegerField, Q, Sum, Value
from django.db.models.functions import Coalesce, Greatest

from .models import UserProgress

ROW_XP = Greatest(
    Coalesce(F("xp_earned"), Value(0)),
    F("score"),
    output_field=IntegerField(),
)


def get_user_total_xp(user):
    if not user or not user.pk:
        return 0
    result = UserProgress.objects.filter(user=user).aggregate(
        total_xp=Coalesce(Sum(ROW_XP), Value(0)),
    )
    return result["total_xp"] or 0


def get_user_completed_levels(user):
    if not user or not user.pk:
        return 0
    return UserProgress.objects.filter(user=user, is_completed=True).count()


def sync_user_score(user):
    total = get_user_total_xp(user)
    if user.score != total:
        user.score = total
        user.save(update_fields=["score"])
    return total


def get_user_level(user):
    xp = get_user_total_xp(user)
    return max(1, xp // 500 + 1)


def get_user_streak(user):
    if not user or not user.pk:
        return 0
    from datetime import timedelta
    from django.utils import timezone

    dates = sorted(
        {
            d
            for d in UserProgress.objects.filter(user=user).values_list(
                "updated_at__date", flat=True
            )
            if d
        },
        reverse=True,
    )
    if not dates:
        return 0

    today = timezone.localdate()
    if dates[0] < today - timedelta(days=1):
        return 0

    streak = 0
    expected = dates[0]
    for day in dates:
        if day == expected:
            streak += 1
            expected -= timedelta(days=1)
        elif day < expected:
            break
    return streak


def build_user_stats(user):
    total_xp = get_user_total_xp(user)
    return {
        "user": user,
        "total_xp": total_xp,
        "level": get_user_level(user),
        "streak": get_user_streak(user),
        "completed_levels": get_user_completed_levels(user),
    }
