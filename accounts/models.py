from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager, Group, Permission


class CustomUserManager(BaseUserManager):
    def create_user(self, phone, nom, password=None, **extra_fields):
        if not phone:
            raise ValueError('Le numéro de téléphone est obligatoire')
        user = self.model(phone=phone, nom=nom, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, nom, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(phone, nom, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField(max_length=20, unique=True)
    nom = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_super_admin = models.BooleanField(default=False)

    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',  # éviter conflit avec AbstractUser
        blank=True,
        help_text='Groupes auxquels appartient cet utilisateur.',
        verbose_name='groupes'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',  # éviter conflit avec AbstractUser
        blank=True,
        help_text='Permissions spécifiques pour cet utilisateur.',
        verbose_name='permissions utilisateur'
    )

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['nom']

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.nom} ({self.phone})"

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Invitation(models.Model):
    code = models.CharField(max_length=100, unique=True)
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code
