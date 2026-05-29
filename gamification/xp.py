from django.db.models import Count, F, IntegerField, Q, Sum, Value
from django.db.models.functions import Coalesce, Greatest

from .models import UserProgress

ROW_XP = Greatest(
    Coalesce(F("xp_earned"), Value(0)),
    F("score"),
    output_field=IntegerField(),
)


def get_user_total_xp(user):
    """Total XP from all level progress (same logic as leaderboard)."""
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
    """Keep User.score in sync with aggregated progress XP."""
    total = get_user_total_xp(user)
    if user.score != total:
        user.score = total
        user.save(update_fields=["score"])
    return total
