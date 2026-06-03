from django.contrib import admin

from .models import (
    ChatMessage,
    ChatReadState,
    ChatRoom,
    FriendRequest,
    Friendship,
    Notification,
    UserPresence,
)

admin.site.register(FriendRequest)
admin.site.register(Friendship)
admin.site.register(Notification)
admin.site.register(ChatRoom)
admin.site.register(ChatMessage)
admin.site.register(ChatReadState)
admin.site.register(UserPresence)
