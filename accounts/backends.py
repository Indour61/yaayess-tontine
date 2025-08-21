from django.contrib.auth.backends import BaseBackend
from .models import CustomUser
from django.contrib.auth.hashers import check_password

class NomBackend(BaseBackend):
    """
    Authentification par nom uniquement
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Ici, username correspond en fait au nom
        try:
            user = CustomUser.objects.get(nom=username)
            if user.check_password(password):
                return user
        except CustomUser.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None
