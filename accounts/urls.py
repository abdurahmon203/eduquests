from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("verify/", views.verify_view, name="verify"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
]
