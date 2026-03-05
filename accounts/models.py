from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, Group, Permission
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .managers import CustomUserManager


class CustomUser(AbstractBaseUser, PermissionsMixin):

    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Le numéro de téléphone doit être au format: '+999999999'. Jusqu'à 15 chiffres autorisés.")
    )

    OPTION_CHOICES = (
        ('1', 'Cotisation & Tontine'),
        ('2', 'Épargne & Crédit'),
    )

    phone = models.CharField(
        _('numéro de téléphone'),
        max_length=17,
        unique=True,
        validators=[phone_regex],
        help_text=_('Numéro de téléphone au format international')
    )

    nom = models.CharField(
        _('nom complet'),
        max_length=150,
        help_text=_('Votre nom complet')
    )

    alias = models.CharField(
        _('alias'),
        max_length=150,
        blank=True,
        null=True,
        help_text=_('Nom alternatif ou alias (optionnel)')
    )

    email = models.EmailField(
        _('adresse email'),
        blank=True,
        null=True,
        help_text=_('Adresse email (optionnelle)')
    )

    option = models.CharField(
        max_length=1,
        choices=OPTION_CHOICES,
        default='1',
        verbose_name=_("Option d'inscription"),
        help_text=_("Option choisie lors de l'inscription")
    )

    # Validation admin
    is_validated = models.BooleanField(default=False)

    validated_at = models.DateTimeField(
        null=True,
        blank=True
    )

    validated_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="validated_users",
        limit_choices_to={"is_staff": True}
    )

    # Acceptation des conditions
    terms_accepted_at = models.DateTimeField(
        null=True,
        blank=True
    )

    terms_version = models.CharField(
        max_length=32,
        null=True,
        blank=True
    )

    is_active = models.BooleanField(
        _('actif'),
        default=True,
        help_text=_('Désigne si cet utilisateur doit être traité comme actif.')
    )

    is_staff = models.BooleanField(
        _('membre du staff'),
        default=False,
        help_text=_('Autorise l’accès à l’administration Django.')
    )

    is_super_admin = models.BooleanField(
        _('super administrateur'),
        default=False,
        help_text=_('Utilisateur avec tous les droits YaayESS.')
    )

    # Relations groupes
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groupes'),
        blank=True,
        related_name="customuser_groups",
        related_query_name="customuser",
    )

    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('permissions utilisateur'),
        blank=True,
        related_name="customuser_permissions",
        related_query_name="customuser",
    )

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['nom']

    objects = CustomUserManager()

    class Meta:
        verbose_name = _('utilisateur')
        verbose_name_plural = _('utilisateurs')
        ordering = ['nom', 'phone']

    def __str__(self):
        if self.alias:
            return f"{self.nom} [{self.alias}] ({self.phone})"
        return f"{self.nom} ({self.phone})"

    def get_full_name(self):
        if self.alias:
            return f"{self.nom} ({self.alias})"
        return self.nom

    def get_short_name(self):
        return self.alias or (self.nom.split()[0] if self.nom else self.phone)

    @property
    def has_accepted_terms(self):
        return bool(self.terms_accepted_at and self.terms_version)

    def save(self, *args, **kwargs):
        """
        Empêche la modification de l'option après l'inscription.
        """
        if self.pk:
            old_user = CustomUser.objects.get(pk=self.pk)
            if old_user.option != self.option:
                raise ValueError("L'option ne peut pas être modifiée après l'inscription.")

        super().save(*args, **kwargs)


# ---------------------------------------------------
# Modèle d'invitation
# ---------------------------------------------------

from django.contrib.auth import get_user_model

User = get_user_model()


class Invitation(models.Model):

    code = models.CharField(
        max_length=100,
        unique=True
    )

    invited_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.code
