from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.views.decorators.http import require_POST

from gamification.xp import build_user_stats

from .forms import UserSearchForm
from .models import FriendRequest, Notification
from .services import (
    accept_friend_request,
    get_friends_queryset,
    get_relationship_status,
    reject_friend_request,
    remove_friendship,
    send_friend_request,
)
from .social import get_social_hub_stats

User = get_user_model()


def _annotate_users(users, viewer):
    from .services import get_pending_request

    annotated = []
    for user in users:
        stats = build_user_stats(user)
        rel = get_relationship_status(viewer, user)
        stats["relationship"] = rel
        stats["is_current_user"] = user.pk == viewer.pk
        if rel == "pending_incoming":
            req = get_pending_request(user, viewer)
            stats["incoming_request_id"] = req.pk if req else None
        annotated.append(stats)
    return annotated


@login_required
def friends_list(request):
    friends = get_friends_queryset(request.user)
    friend_stats = _annotate_users(friends, request.user)
    return render(
        request,
        "friends/list.html",
        {
            "friends": friend_stats,
            "hub_stats": get_social_hub_stats(request.user),
        },
    )


@login_required
def friends_search(request):
    form = UserSearchForm(request.GET or None)
    query = form.cleaned_data["q"].strip() if form.is_valid() and form.cleaned_data["q"] else ""
    results = []

    if query:
        users = (
            User.objects.filter(username__icontains=query, is_active=True)
            .exclude(pk=request.user.pk)
            .order_by("username")[:20]
        )
        results = _annotate_users(users, request.user)

    if request.GET.get("partial") == "1":
        return render(
            request,
            "friends/_search_results.html",
            {"results": results, "query": query},
        )

    return render(
        request,
        "friends/search.html",
        {
            "form": form,
            "results": results,
            "query": query,
            "hub_stats": get_social_hub_stats(request.user),
        },
    )


@login_required
def friend_requests(request):
    incoming = (
        FriendRequest.objects.filter(to_user=request.user, accepted=False)
        .select_related("from_user")
        .order_by("-created_at")
    )
    outgoing = (
        FriendRequest.objects.filter(from_user=request.user, accepted=False)
        .select_related("to_user")
        .order_by("-created_at")
    )

    incoming_stats = [
        {"request": req, **build_user_stats(req.from_user)}
        for req in incoming
    ]
    outgoing_stats = [
        {"request": req, **build_user_stats(req.to_user)}
        for req in outgoing
    ]

    return render(
        request,
        "friends/requests.html",
        {
            "incoming": incoming_stats,
            "outgoing": outgoing_stats,
            "hub_stats": get_social_hub_stats(request.user),
        },
    )


@login_required
def friends_leaderboard(request):
    friends = list(get_friends_queryset(request.user))
    participants = friends + [request.user]
    hub_stats = get_social_hub_stats(request.user)

    ranked = []
    for user in participants:
        stats = build_user_stats(user)
        stats["is_current_user"] = user.pk == request.user.pk
        ranked.append(stats)

    ranked.sort(key=lambda x: (-x["total_xp"], x["user"].username))

    leaderboard = []
    for rank, entry in enumerate(ranked, start=1):
        entry["rank"] = rank
        leaderboard.append(entry)

    if len(leaderboard) >= 3:
        podium = [leaderboard[1], leaderboard[0], leaderboard[2]]
    elif len(leaderboard) == 2:
        podium = [leaderboard[1], leaderboard[0]]
    else:
        podium = leaderboard[:1]

    return render(
        request,
        "friends/leaderboard.html",
        {
            "leaderboard": leaderboard,
            "podium": podium,
            "has_entries": bool(leaderboard),
            "hub_stats": hub_stats,
            "friends_count": hub_stats["friends_count"],
        },
    )


@login_required
def notifications_list(request):
    notifications = (
        Notification.objects.filter(recipient=request.user)
        .select_related("sender")
        .order_by("-created_at")
    )
    return render(
        request,
        "friends/notifications.html",
        {"notifications": notifications},
    )


@login_required
@require_POST
def add_friend(request, user_id):
    target = get_object_or_404(User, pk=user_id, is_active=True)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    try:
        send_friend_request(request.user, target)
        rel = get_relationship_status(request.user, target)
        incoming_id = None
        if rel == "pending_incoming":
            from .services import get_pending_request

            req = get_pending_request(target, request.user)
            incoming_id = req.pk if req else None

        if is_ajax:
            return JsonResponse(
                {
                    "ok": True,
                    "relationship": rel,
                    "incoming_request_id": incoming_id,
                    "username": target.username,
                }
            )
        messages.success(request, f"Friend request sent to {target.username}.")
    except ValueError as exc:
        if is_ajax:
            return JsonResponse({"ok": False, "error": str(exc)}, status=400)
        messages.error(request, str(exc))
    except PermissionError as exc:
        if is_ajax:
            return JsonResponse({"ok": False, "error": str(exc)}, status=403)
        messages.error(request, str(exc))

    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "friends_search"
    return redirect(next_url)


@login_required
@require_POST
def accept_friend(request, request_id):
    friend_request = get_object_or_404(
        FriendRequest,
        pk=request_id,
        to_user=request.user,
        accepted=False,
    )
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    username = friend_request.from_user.username

    try:
        accept_friend_request(friend_request, request.user)
        if is_ajax:
            return JsonResponse(
                {
                    "ok": True,
                    "relationship": "friends",
                    "username": username,
                }
            )
        messages.success(request, f"You and {username} are now friends!")
    except (ValueError, PermissionError) as exc:
        if is_ajax:
            return JsonResponse({"ok": False, "error": str(exc)}, status=400)
        messages.error(request, str(exc))

    return redirect(request.POST.get("next", "friend_requests"))


@login_required
@require_POST
def reject_friend(request, request_id):
    friend_request = get_object_or_404(
        FriendRequest,
        pk=request_id,
        to_user=request.user,
        accepted=False,
    )
    try:
        username = friend_request.from_user.username
        reject_friend_request(friend_request, request.user)
        messages.success(request, f"Declined friend request from {username}.")
    except (ValueError, PermissionError) as exc:
        messages.error(request, str(exc))
    return redirect(request.POST.get("next", "friend_requests"))


@login_required
@require_POST
def remove_friend(request, user_id):
    friend = get_object_or_404(User, pk=user_id, is_active=True)
    try:
        remove_friendship(request.user, friend)
        messages.success(request, f"Removed {friend.username} from your friends.")
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect(request.POST.get("next", "friends_list"))


@login_required
@require_POST
def mark_notifications_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(
        is_read=True
    )
    next_url = request.POST.get("next") or "notifications_list"
    return redirect(next_url)


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    note = get_object_or_404(
        Notification,
        pk=notification_id,
        recipient=request.user,
    )
    note.is_read = True
    note.save(update_fields=["is_read"])
    return redirect(request.POST.get("next", "notifications_list"))
