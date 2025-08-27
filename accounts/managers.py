from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """
    Manager personnalisé pour le modèle CustomUser.
    """

    def create_user(self, phone, nom, password=None, **extra_fields):
        """
        Crée et retourne un utilisateur avec un numéro de téléphone et un nom.
        """
        if not phone:
            raise ValueError(_('Le numéro de téléphone doit être renseigné.'))
        if not nom:
            raise ValueError(_('Le nom complet doit être renseigné.'))

        phone = self.normalize_email(phone)  # Normalise comme pour email, mais on peut laisser tel quel
        user = self.model(phone=phone, nom=nom, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, nom, password=None, **extra_fields):
        """
        Crée et retourne un superutilisateur.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_super_admin', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Le superutilisateur doit avoir is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Le superutilisateur doit avoir is_superuser=True.'))

        return self.create_user(phone, nom, password, **extra_fields)
