from django.db.models import Count, F, IntegerField, Q, Sum, Value
from django.db.models.functions import Coalesce, Greatest
from django.shortcuts import render

from .models import UserProgress


def leaderboard(request):
    row_xp = Greatest(
        Coalesce(F("xp_earned"), Value(0)),
        F("score"),
        output_field=IntegerField(),
    )

    stats = (
        UserProgress.objects.values("user_id", "user__username")
        .annotate(
            total_xp=Coalesce(Sum(row_xp), Value(0)),
            completed_levels=Count("pk", filter=Q(is_completed=True)),
        )
        .filter(total_xp__gt=0)
        .order_by("-total_xp", "user__username")[:10]
    )

    leaderboard_entries = []
    for rank, row in enumerate(stats, start=1):
        is_current = (
            request.user.is_authenticated
            and row["user_id"] == request.user.pk
        )
        leaderboard_entries.append(
            {
                "rank": rank,
                "username": row["user__username"],
                "total_xp": row["total_xp"],
                "completed_levels": row["completed_levels"],
                "is_current_user": is_current,
            }
        )

    current_user_entry = None
    current_user_in_top_ten = False
    if request.user.is_authenticated:
        for entry in leaderboard_entries:
            if entry["is_current_user"]:
                current_user_entry = entry
                current_user_in_top_ten = True
                break

        if current_user_entry is None:
            user_stats = (
                UserProgress.objects.filter(user=request.user)
                .aggregate(
                    total_xp=Coalesce(Sum(row_xp), Value(0)),
                    completed_levels=Count("pk", filter=Q(is_completed=True)),
                )
            )
            if user_stats["total_xp"] and user_stats["total_xp"] > 0:
                higher_count = (
                    UserProgress.objects.values("user_id")
                    .annotate(total_xp=Coalesce(Sum(row_xp), Value(0)))
                    .filter(total_xp__gt=user_stats["total_xp"])
                    .count()
                )
                current_user_entry = {
                    "rank": higher_count + 1,
                    "username": request.user.username,
                    "total_xp": user_stats["total_xp"],
                    "completed_levels": user_stats["completed_levels"],
                    "is_current_user": True,
                }

    return render(
        request,
        "leaderboard.html",
        {
            "leaderboard": leaderboard_entries,
            "current_user_entry": current_user_entry,
            "show_current_user_footer": (
                request.user.is_authenticated
                and current_user_entry is not None
                and not current_user_in_top_ten
            ),
            "has_entries": bool(leaderboard_entries),
        },
    )
