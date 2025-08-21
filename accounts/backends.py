from django.contrib.auth.backends import BaseBackend
from .models import CustomUser

class NomBackend(BaseBackend):
    """
    Authentifie un utilisateur via son nom et mot de passe.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = CustomUser.objects.get(nom=username)
        except CustomUser.DoesNotExist:
            return None

        if user.check_password(password) and user.is_active:
            return user
        return None

    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None
