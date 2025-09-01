from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager, Group, Permission
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    def create_user(self, phone, nom, password=None, **extra_fields):
        """
        Crée et enregistre un utilisateur avec le numéro de téléphone, le nom et le mot de passe.
        """
        if not phone:
            raise ValueError(_('Le numéro de téléphone est obligatoire'))
        if not nom:
            raise ValueError(_('Le nom est obligatoire'))

        user = self.model(
            phone=phone,
            nom=nom,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, nom, password=None, **extra_fields):
        """
        Crée et enregistre un superutilisateur avec les privilèges d'administration.
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


from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, Group, Permission
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from .managers import CustomUserManager

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, Group, Permission
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from .managers import CustomUserManager
from django.utils import timezone

class CustomUser(AbstractBaseUser, PermissionsMixin):
    # Validateur pour le format de numéro de téléphone
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

    # Nouveau champ option
    option = models.CharField(
        max_length=1,
        choices=OPTION_CHOICES,
        default='1',
        verbose_name="Option d'inscription",
        help_text="Option choisie lors de l'inscription"
    )

    is_validated = models.BooleanField(default=False)  # ✅ Nouveau champ
    date_joined = models.DateTimeField(
        _("date d'inscription"),
        default=timezone.now
    )

    is_active = models.BooleanField(
        _('actif'),
        default=True,
        help_text=_('Désigne si cet utilisateur doit être traité comme actif.')
    )

    is_staff = models.BooleanField(
        _('membre du staff'),
        default=False,
        help_text=_('Désigne si l\'utilisateur peut se connecter à l\'interface d\'administration.')
    )

    is_super_admin = models.BooleanField(
        _('super administrateur'),
        default=False,
        help_text=_('Désigne si l\'utilisateur a tous les droits sans limitation.')
    )

    # Relations avec les groupes et permissions
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groupes'),
        blank=True,
        help_text=_(
            'Les groupes auxquels appartient cet utilisateur. Un utilisateur obtiendra '
            'toutes les permissions accordées à chacun de ses groupes.'
        ),
        related_name="customuser_groups",
        related_query_name="customuser",
    )

    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('permissions utilisateur'),
        blank=True,
        help_text=_('Permissions spécifiques pour cet utilisateur.'),
        related_name="customuser_permissions",
        related_query_name="customuser",
    )

    # Champs requis pour le modèle d'utilisateur personnalisé
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['nom']

    objects = CustomUserManager()

    class Meta:
        verbose_name = _('utilisateur')
        verbose_name_plural = _('utilisateurs')
        ordering = ['nom', 'phone']

    def __str__(self):
        return f"{self.nom} ({self.phone})" if not self.alias else f"{self.nom} [{self.alias}] ({self.phone})"

    def get_full_name(self):
        """
        Retourne le nom complet de l'utilisateur.
        """
        return f"{self.nom} ({self.alias})" if self.alias else self.nom

    def get_short_name(self):
        """
        Retourne une version courte du nom de l'utilisateur.
        """
        return self.alias or self.nom.split()[0] if self.nom else self.phone


from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Invitation(models.Model):
    code = models.CharField(max_length=100, unique=True)
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code
