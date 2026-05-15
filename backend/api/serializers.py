from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers

from api.models import Appointment, ChatSession, User


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(max_length=255)

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_email(self, value):
        email = value.lower()
        if User.objects.filter(email=email, business__isnull=True).exists():
            raise serializers.ValidationError("Email already registered.")
        return email

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            full_name=validated_data["full_name"],
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs["email"].lower()
        user = authenticate(
            request=self.context.get("request"),
            email=email,
            password=attrs["password"],
        )
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("Account is disabled.")
        attrs["user"] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "full_name", "business_id", "created_at")
        read_only_fields = fields


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = (
            "id",
            "title",
            "starts_at",
            "ends_at",
            "status",
            "notes",
            "source",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "source", "created_at", "updated_at")

    def validate(self, attrs):
        starts = attrs.get("starts_at", getattr(self.instance, "starts_at", None))
        ends = attrs.get("ends_at", getattr(self.instance, "ends_at", None))
        if starts and ends and ends <= starts:
            raise serializers.ValidationError("ends_at must be after starts_at.")
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        return Appointment.objects.create(
            user=user,
            business=user.business,
            source="form",
            **validated_data,
        )


class ChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = (
            "id",
            "title",
            "messages",
            "metadata",
            "last_message_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class ChatMessageSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=4000)
    session_id = serializers.UUIDField(required=False)
    confirm_booking = serializers.BooleanField(default=False)


class ChatSessionCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
