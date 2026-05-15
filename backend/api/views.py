import asyncio

from django.shortcuts import get_object_or_404
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from api.models import Appointment, ChatSession
from api.serializers import (
    AppointmentSerializer,
    ChatMessageSerializer,
    ChatSessionCreateSerializer,
    ChatSessionSerializer,
    LoginSerializer,
    SignupSerializer,
    UserSerializer,
)
from api.services.chat import process_chat_message


def _tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


@method_decorator(ratelimit(key="ip", rate="10/m", method="POST", block=True), name="dispatch")
class SignupView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"user": UserSerializer(user).data, "tokens": _tokens_for_user(user)},
            status=status.HTTP_201_CREATED,
        )


@method_decorator(ratelimit(key="ip", rate="10/m", method="POST", block=True), name="dispatch")
class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        return Response(
            {"user": UserSerializer(user).data, "tokens": _tokens_for_user(user)},
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class AppointmentListCreateView(generics.ListCreateAPIView):
    serializer_class = AppointmentSerializer

    def get_queryset(self):
        return Appointment.objects.filter(user=self.request.user).order_by("-starts_at")


class AppointmentDetailView(generics.RetrieveAPIView):
    serializer_class = AppointmentSerializer

    def get_queryset(self):
        return Appointment.objects.filter(user=self.request.user)


class ChatSessionListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatSessionSerializer

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user).order_by("-updated_at")

    def create(self, request, *args, **kwargs):
        body = ChatSessionCreateSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        session = ChatSession.objects.create(
            user=request.user,
            business=request.user.business,
            title=body.validated_data.get("title") or "New chat",
            messages=[],
            metadata={},
        )
        return Response(ChatSessionSerializer(session).data, status=status.HTTP_201_CREATED)


class ChatSessionDetailView(generics.RetrieveAPIView):
    serializer_class = ChatSessionSerializer

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)


@method_decorator(ratelimit(key="user", rate="60/m", method="POST", block=True), name="dispatch")
class ChatMessageView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "chat"

    def post(self, request):
        serializer = ChatMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if data.get("session_id"):
            session = get_object_or_404(
                ChatSession, id=data["session_id"], user=request.user
            )
        else:
            session = ChatSession.objects.create(
                user=request.user,
                business=request.user.business,
                title="Booking chat",
                messages=[],
                metadata={},
            )

        result = asyncio.run(
            process_chat_message(
                session,
                request.user,
                data["content"],
                confirm_booking=data.get("confirm_booking", False),
            )
        )
        return Response(result, status=status.HTTP_200_OK)
