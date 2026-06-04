from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from levels.models import Level
from quizzes.models import Question
from friends.models import Friendship, ChatMessage
from gamification.models import UserProgress


def is_admin_user(user):
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_admin_user)
def admin_dashboard(request):
    """Admin dashboard with site statistics and management tools"""
    
    # Calculate statistics
    total_users = User.objects.count()
    total_quizzes = Level.objects.count()
    total_questions = Question.objects.count()
    total_friendships = Friendship.objects.count()
    total_messages = ChatMessage.objects.count()
    
    # Calculate total XP earned
    total_xp_earned = UserProgress.objects.aggregate(total=Sum('xp_earned'))['total'] or 0
    
    # Recent users (last 7 days)
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_users = User.objects.filter(date_joined__gte=seven_days_ago).order_by('-date_joined')[:10]
    
    # Recent activity (last 24 hours)
    one_day_ago = timezone.now() - timedelta(days=1)
    recent_activity = []
    
    # Recent quiz completions
    recent_progress = UserProgress.objects.filter(
        updated_at__gte=one_day_ago,
        is_completed=True
    ).select_related('user', 'level').order_by('-updated_at')[:5]
    
    for progress in recent_progress:
        recent_activity.append({
            'type': 'quiz_completion',
            'user': progress.user.username,
            'details': f"Completed {progress.level.title}",
            'time': progress.updated_at
        })
    
    # Recent friendships
    recent_friendships = Friendship.objects.filter(
        created_at__gte=one_day_ago
    ).order_by('-created_at')[:5]

    for friendship in recent_friendships:
        recent_activity.append({
            'type': 'friendship',
            'user': friendship.user1.username,
            'details': f"Became friends with {friendship.user2.username}",
            'time': friendship.created_at
        })
    
    # Sort recent activity by time
    recent_activity.sort(key=lambda x: x['time'], reverse=True)
    recent_activity = recent_activity[:10]
    
    # User growth data for charts (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    user_growth_data = []
    for i in range(30):
        day = thirty_days_ago + timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count = User.objects.filter(date_joined__gte=day_start, date_joined__lt=day_end).count()
        user_growth_data.append({
            'date': day.strftime('%Y-%m-%d'),
            'count': count
        })
    
    context = {
        'total_users': total_users,
        'total_quizzes': total_quizzes,
        'total_questions': total_questions,
        'total_friendships': total_friendships,
        'total_messages': total_messages,
        'total_xp_earned': total_xp_earned,
        'recent_users': recent_users,
        'recent_activity': recent_activity,
        'user_growth_data': user_growth_data,
    }
    
    return render(request, 'admin/dashboard.html', context)
