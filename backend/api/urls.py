from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from api import views

urlpatterns = [
    path("auth/signup/", views.SignupView.as_view(), name="auth-signup"),
    path("auth/login/", views.LoginView.as_view(), name="auth-login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("auth/me/", views.MeView.as_view(), name="auth-me"),
    path("appointments/", views.AppointmentListCreateView.as_view(), name="appointments-list"),
    path(
        "appointments/<uuid:pk>/",
        views.AppointmentDetailView.as_view(),
        name="appointments-detail",
    ),
    path("chat/sessions/", views.ChatSessionListCreateView.as_view(), name="chat-sessions"),
    path(
        "chat/sessions/<uuid:pk>/",
        views.ChatSessionDetailView.as_view(),
        name="chat-session-detail",
    ),
    path("chat/messages/", views.ChatMessageView.as_view(), name="chat-message"),
]
