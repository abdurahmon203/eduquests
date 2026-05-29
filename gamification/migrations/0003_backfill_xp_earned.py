from django.db import migrations
from django.db.models import F


def backfill_xp_earned(apps, schema_editor):
    UserProgress = apps.get_model("gamification", "UserProgress")
    UserProgress.objects.filter(xp_earned=0, score__gt=0).update(
        xp_earned=F("score")
    )
    # Passed quizzes stored score only; add completion bonus where applicable
    UserProgress.objects.filter(
        xp_earned__lt=100,
        is_completed=True,
        score__gte=50,
    ).update(xp_earned=F("score") + 50)


class Migration(migrations.Migration):

    dependencies = [
        ("gamification", "0002_userprogress_xp_earned"),
    ]

    operations = [
        migrations.RunPython(backfill_xp_earned, migrations.RunPython.noop),
    ]
