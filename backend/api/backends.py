from django.contrib.auth.backends import ModelBackend

from api.models import User


class EmailAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        email = (kwargs.get("email") or username or "").lower()
        if not email or password is None:
            return None
        try:
            user = User.objects.get(email=email, business__isnull=True)
        except User.DoesNotExist:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
