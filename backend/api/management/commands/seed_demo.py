from datetime import datetime, timezone as dt_timezone

from django.core.management.base import BaseCommand
from django.utils import timezone

from api.models import Appointment, AppointmentStatus, Business, ChatSession, User


class Command(BaseCommand):
    help = "Seed demo business, user, appointment, and chat session"

    def handle(self, *args, **options):
        business, _ = Business.objects.update_or_create(
            id="11111111-1111-1111-1111-111111111111",
            defaults={"name": "Acme Dental Demo Org"},
        )

        user, created = User.objects.get_or_create(
            email="demo@example.com",
            business=None,
            defaults={"full_name": "Demo User"},
        )
        if created:
            user.set_password("Password123!")
            user.save()
            self.stdout.write(self.style.SUCCESS("Created demo@example.com / Password123!"))
        else:
            self.stdout.write("Demo user already exists")

        Appointment.objects.update_or_create(
            id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            defaults={
                "user": user,
                "business": None,
                "title": "Consultation",
                "starts_at": datetime(2026, 5, 20, 10, 0, tzinfo=dt_timezone.utc),
                "ends_at": datetime(2026, 5, 20, 10, 30, tzinfo=dt_timezone.utc),
                "status": AppointmentStatus.SCHEDULED,
                "notes": "First visit",
                "source": "form",
            },
        )

        ChatSession.objects.update_or_create(
            id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            defaults={
                "user": user,
                "business": None,
                "title": "Booking help",
                "messages": [
                    {
                        "role": "user",
                        "content": "I need Tuesday afternoon",
                        "ts": timezone.now().isoformat(),
                    },
                    {
                        "role": "assistant",
                        "content": "Which Tuesday and what time works best?",
                        "ts": timezone.now().isoformat(),
                    },
                ],
                "metadata": {"model": "mistral-small-latest"},
                "last_message_at": timezone.now(),
            },
        )

        self.stdout.write(self.style.SUCCESS("Seed complete"))
