from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, Group, Permission
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from .managers import CustomUserManager

class CustomUser(AbstractBaseUser, PermissionsMixin):

    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Le numéro doit être au format '+999999999'. Maximum 15 chiffres.")
    )

    OPTION_CHOICES = (
        ('1', 'Cotisation & Tontine'),
        ('2', 'Épargne & Crédit'),
    )

    phone = models.CharField(
        _('numéro de téléphone'),
        max_length=17,
        unique=True,
        db_index=True,
        validators=[phone_regex]
    )

    nom = models.CharField(
        _('nom complet'),
        max_length=150,
        db_index=True
    )

    alias = models.CharField(
        _('alias'),
        max_length=150,
        blank=True
    )

    email = models.EmailField(
        _('adresse email'),
        blank=True
    )

    # -----------------------------
    # Localisation utilisateur
    # -----------------------------

    pays = models.CharField(
        _('pays'),
        max_length=100,
        blank=True,
        db_index=True
    )

    ville = models.CharField(
        _('ville'),
        max_length=100,
        blank=True,
        db_index=True
    )

    option = models.CharField(
        max_length=1,
        choices=OPTION_CHOICES,
        default='1'
    )

    # -----------------------------
    # Abonnement YaayESS
    # -----------------------------

    abonnement_actif = models.BooleanField(
        default=True,
        db_index=True
    )

    date_activation = models.DateTimeField(
        null=True,
        blank=True
    )

    date_expiration = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True
    )

    # -----------------------------
    # Validation admin
    # -----------------------------

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

    # -----------------------------
    # Conditions d'utilisation
    # -----------------------------

    terms_accepted_at = models.DateTimeField(
        null=True,
        blank=True
    )

    terms_version = models.CharField(
        max_length=32,
        blank=True
    )

    # -----------------------------
    # Permissions Django
    # -----------------------------

    is_active = models.BooleanField(default=True)

    is_staff = models.BooleanField(
        default=False,
        help_text=_("Autorise l’accès à l’administration Django.")
    )

    is_super_admin = models.BooleanField(
        default=False,
        help_text=_("Utilisateur avec tous les droits YaayESS.")
    )

    # -----------------------------
    # Timestamps
    # -----------------------------

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    # -----------------------------
    # Relations Django
    # -----------------------------

    groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name="yaayess_users"
    )

    user_permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name="yaayess_permissions"
    )

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['nom']

    objects = CustomUserManager()

    class Meta:
        verbose_name = _('utilisateur')
        verbose_name_plural = _('utilisateurs')
        ordering = ['nom']

        indexes = [
            models.Index(fields=["phone"]),
            models.Index(fields=["nom"]),
            models.Index(fields=["abonnement_actif"]),
            models.Index(fields=["date_expiration"]),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=['phone'],
                name='unique_phone_user'
            )
        ]

    def __str__(self):
        return f"{self.nom or 'Utilisateur'} ({self.phone})"

    def get_full_name(self):
        return f"{self.nom} ({self.alias})" if self.alias else self.nom

    def get_short_name(self):
        return self.alias or (self.nom.split()[0] if self.nom else self.phone)

    @property
    def has_accepted_terms(self):
        return bool(self.terms_accepted_at and self.terms_version)

    def save(self, *args, **kwargs):
        """
        Empêche la modification de l'option après inscription.
        """
        if self.pk:
            old_option = CustomUser.objects.filter(
                pk=self.pk
            ).values_list("option", flat=True).first()

            if old_option and old_option != self.option:
                raise ValueError("L'option ne peut pas être modifiée après l'inscription.")

        super().save(*args, **kwargs)


# ---------------------------------------------------
# Modèle Invitation
# ---------------------------------------------------

User = get_user_model()


class Invitation(models.Model):

    code = models.CharField(
        max_length=100,
        unique=True,
        db_index=True
    )

    invited_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="invitations"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["code"]),
        ]

    def __str__(self):
        return f"Invitation {self.code}"

class Group(models.Model):

    nom = models.CharField(max_length=200)

    admin = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.CASCADE,
        related_name="admin_groups",
        db_index=True
    )

    montant_base = models.PositiveIntegerField()

    members_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["admin"]),
            models.Index(fields=["is_active"]),
        ]

    def commission_par_membre(self):

        if self.members_count <= 200:
            return 150
        elif self.members_count <= 500:
            return 100
        return 80

    def commission_totale(self):

        return self.members_count * self.commission_par_membre()

    def __str__(self):
        return self.nom

class Member(models.Model):

    user = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.CASCADE,
        db_index=True
    )

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="members",
        db_index=True
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=["user", "group"],
                name="unique_member_group"
            )
        ]

        indexes = [
            models.Index(fields=["group"]),
            models.Index(fields=["user"]),
            models.Index(fields=["group", "user"]),
        ]

    def save(self, *args, **kwargs):

        is_new = self.pk is None

        super().save(*args, **kwargs)

        if is_new:
            Group.objects.filter(id=self.group.id).update(
                members_count=models.F("members_count") + 1
            )

    def delete(self, *args, **kwargs):

        group_id = self.group.id

        super().delete(*args, **kwargs)

        Group.objects.filter(id=group_id).update(
            members_count=models.F("members_count") - 1
        )

    def __str__(self):
        return f"{self.user.nom} - {self.group.nom}"


class Versement(models.Model):

    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name="versements",
        db_index=True
    )

    montant = models.PositiveIntegerField()

    commission = models.PositiveIntegerField()

    total = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:

        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["member"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.member} - {self.montant} FCFA"



from decimal import Decimal

def save(self, *args, **kwargs):

    if not self.frais:
        self.frais = (self.montant * Decimal("0.01")).quantize(Decimal("1"))

    super().save(*args, **kwargs)


from django.db import models


class Payment(models.Model):

    member = models.ForeignKey("Member", on_delete=models.CASCADE)

    montant = models.DecimalField(max_digits=10, decimal_places=2)

    receipt_pdf = models.FileField(upload_to="receipts/", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Paiement {self.montant} - {self.member}"


class Notification(models.Model):
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message

# models.py

from django.db import models
from epargnecredit.models import Group


class Invoice(models.Model):

    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('paid', 'Payée'),
        ('overdue', 'En retard'),
    ]

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="factures")

    mois = models.DateField()

    montant_cotisation = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    montant_epargne = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    montant_remboursement = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    total = models.DecimalField(max_digits=10, decimal_places=2)

    # 🔥 NUMERO FACTURE
    numero = models.CharField(max_length=50, unique=True, blank=True)
#    numero = models.CharField(max_length=50, blank=True, null=True)
    statut = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.numero} - {self.group.nom} - {self.mois}"

    # 🔥 GÉNÉRATION AUTOMATIQUE DU NUMERO
    def save(self, *args, **kwargs):

        if not self.numero:
            year = self.mois.year

            last_invoice = Invoice.objects.filter(
                numero__startswith=f"YAAY-{year}"
            ).order_by('-id').first()

            if last_invoice and last_invoice.numero:
                last_number = int(last_invoice.numero.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.numero = f"YAAY-{year}-{str(new_number).zfill(4)}"

        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('group', 'mois')
        ordering = ['-date_creation']


from django.db import transaction

def save(self, *args, **kwargs):

    if not self.numero:
        year = self.mois.year

        with transaction.atomic():

            last_invoice = Invoice.objects.select_for_update().filter(
                numero__startswith=f"YAAY-{year}"
            ).order_by('-numero').first()  # ✅ IMPORTANT

            if last_invoice and last_invoice.numero:
                last_number = int(last_invoice.numero.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.numero = f"YAAY-{year}-{str(new_number).zfill(4)}"

    super().save(*args, **kwargs)


# accounts/models.py

import random
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class OTPVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_validated = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

    @staticmethod
    def generate_code():
        return str(random.randint(100000, 999999))

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class OTPAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.ForeignKey('OTPVerification', on_delete=models.CASCADE)

    entered_code = models.CharField(max_length=6)
    success = models.BooleanField(default=False)

    ip_address = models.GenericIPAddressField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {'SUCCESS' if self.success else 'FAIL'}"

