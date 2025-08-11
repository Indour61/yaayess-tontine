from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

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
        return self.create_user(phone, nom, password, **extra_fields)

from django.contrib.auth.models import Group, Permission
from django.db import models

class CustomUser(AbstractBaseUser, PermissionsMixin):
    # tes champs
    phone = models.CharField(max_length=20, unique=True)
    nom = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_super_admin = models.BooleanField(default=False)

    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',  # changer related_name pour éviter conflit
        blank=True,
        help_text='Groupes auxquels appartient cet utilisateur.',
        verbose_name='groupes'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',  # changer related_name aussi
        blank=True,
        help_text='Permissions spécifiques pour cet utilisateur.',
        verbose_name='permissions utilisateur'
    )

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['nom']

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.nom} ({self.phone})"

