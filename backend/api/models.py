import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Business(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "businesses"

    def __str__(self) -> str:
        return self.name


class UserManager(BaseUserManager):
    def create_user(self, email: str, password: str | None, full_name: str, **extra):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email.lower(), full_name=full_name, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None, full_name: str = "Admin", **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(email, password, full_name, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(
        Business,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users",
        db_column="business_id",
    )
    email = models.EmailField(unique=False)
    full_name = models.TextField()
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table = "users"
        constraints = [
            models.UniqueConstraint(
                fields=["email", "business"],
                name="users_email_per_business_unique",
            ),
            models.UniqueConstraint(
                fields=["email"],
                condition=Q(business__isnull=True),
                name="users_email_global_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["business", "email"], name="idx_users_business_email"),
        ]

    def __str__(self) -> str:
        return self.email


class AppointmentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SCHEDULED = "scheduled", "Scheduled"
    CANCELLED = "cancelled", "Cancelled"
    COMPLETED = "completed", "Completed"


class Appointment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="appointments", db_column="user_id"
    )
    business = models.ForeignKey(
        Business,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="appointments",
        db_column="business_id",
    )
    title = models.TextField()
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.SCHEDULED,
    )
    notes = models.TextField(blank=True, null=True)
    source = models.TextField(default="form")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "appointments"
        indexes = [
            models.Index(fields=["user", "-starts_at"], name="idx_appt_user_starts"),
            models.Index(fields=["business", "-starts_at"], name="idx_appt_business_starts"),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(ends_at__gt=models.F("starts_at")),
                name="appointments_time_range",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.starts_at})"


class ChatSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="chat_sessions", db_column="user_id"
    )
    business = models.ForeignKey(
        Business,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="chat_sessions",
        db_column="business_id",
    )
    title = models.TextField(blank=True, null=True)
    messages = models.JSONField(default=list)
    metadata = models.JSONField(default=dict)
    last_message_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "chat_sessions"
        indexes = [
            models.Index(fields=["user", "-updated_at"], name="idx_chat_user_updated"),
        ]

    def append_message(self, role: str, content: str) -> dict:
        entry = {
            "role": role,
            "content": content,
            "ts": timezone.now().isoformat(),
        }
        self.messages = [*self.messages, entry]
        self.last_message_at = timezone.now()
        return entry
