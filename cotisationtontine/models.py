from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid


# =====================================================
# GROUPE TONTINE
# =====================================================

class Group(models.Model):

    nom = models.CharField(max_length=255)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_reset = models.DateTimeField(null=True, blank=True)

    code_invitation = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    invitation_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="groupes_administres_tontine"
    )

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    montant_base = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    montant_fixe_gagnant = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)

    prochain_gagnant = models.ForeignKey(
        'GroupMember',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="groupes_prochain_gagnant"
    )

    class Meta:
        ordering = ['-date_creation']

    def __str__(self):
        return self.nom


# =====================================================
# MEMBRE
# =====================================================

class GroupMember(models.Model):

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='membres')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    alias = models.CharField(max_length=100, blank=True, null=True)
    montant = models.DecimalField(max_digits=12, decimal_places=0, default=0)

    actif = models.BooleanField(default=True)
    exit_liste = models.BooleanField(default=False)

    date_ajout = models.DateTimeField(auto_now_add=True)
    date_joined = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('group', 'user')

    def __str__(self):
        return f"{self.user} - {self.group.nom}"


# =====================================================
# VERSEMENT CAISSE
# =====================================================

class Versement(models.Model):

    STATUT_CHOICES = (
        ("EN_ATTENTE", "En attente"),
        ("VALIDE", "Validé"),
        ("REFUSE", "Refusé"),
    )

    member = models.ForeignKey(
        GroupMember,
        on_delete=models.CASCADE,
        related_name='versements'
    )

    montant = models.DecimalField(max_digits=12, decimal_places=0)
    frais = models.DecimalField(max_digits=12, decimal_places=0, default=Decimal("0"))

    methode = models.CharField(max_length=20, default="CAISSE")

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="EN_ATTENTE"
    )

    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="versements_valides_tontine"
    )

    date_creation = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-date_creation"]

    def __str__(self):
        return f"{self.member.user} - {self.montant} FCFA ({self.statut})"

    @property
    def montant_total(self):
        return self.montant + self.frais


# =====================================================
# TIRAGE (AVEC CYCLE NUMBER)
# =====================================================

class Tirage(models.Model):

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="tirages"
    )

    gagnant = models.ForeignKey(
        GroupMember,
        on_delete=models.CASCADE,
        related_name="tirages_gagnes"
    )

    montant = models.DecimalField(max_digits=12, decimal_places=0)

    cycle_number = models.PositiveIntegerField(default=1)

    date_tirage = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_tirage"]

    def __str__(self):
        return f"Groupe: {self.group.nom} | Cycle {self.cycle_number}"


# =====================================================
# HISTORIQUE ACTIONS
# =====================================================

class ActionLog(models.Model):

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="action_logs",
        null=True,
        blank=True
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    action = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} - {self.user}"


# =====================================================
# INVITATION
# =====================================================

class Invitation(models.Model):

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="invitations"
    )

    phone = models.CharField(max_length=20)

    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(days=7)

    def __str__(self):
        return f"Invitation {self.phone} - {self.group.nom}"


