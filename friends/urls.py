from django.urls import path

from . import views

urlpatterns = [
    path("friends/", views.friends_list, name="friends_list"),
    path("friends/search/", views.friends_search, name="friends_search"),
    path("friends/requests/", views.friend_requests, name="friend_requests"),
    path("friends/leaderboard/", views.friends_leaderboard, name="friends_leaderboard"),
    path("notifications/", views.notifications_list, name="notifications_list"),
    path("friends/add/<int:user_id>/", views.add_friend, name="add_friend"),
    path("friends/accept/<int:request_id>/", views.accept_friend, name="accept_friend"),
    path("friends/reject/<int:request_id>/", views.reject_friend, name="reject_friend"),
    path("friends/remove/<int:user_id>/", views.remove_friend, name="remove_friend"),
    path(
        "notifications/read/",
        views.mark_notifications_read,
        name="mark_notifications_read",
    ),
    path(
        "notifications/<int:notification_id>/read/",
        views.mark_notification_read,
        name="mark_notification_read",
    ),
]
