from django.db import models
from django.conf import settings
from django.db.models import Q, UniqueConstraint
from django.utils import timezone
from decimal import Decimal
import uuid


# =========================================================
# GROUPE
# =========================================================

class Group(models.Model):

    nom = models.CharField(max_length=255)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_reset = models.DateTimeField(null=True, blank=True)

    code_invitation = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    invitation_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="groupes_administres_ec"
    )

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    montant_base = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    montant_fixe_gagnant = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)

    prochain_gagnant = models.ForeignKey(
        'GroupMember',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="groupes_prochain_gagnant_ec"
    )

    membres_ec = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='GroupMember',
        related_name='groupes_ec'
    )

    is_remboursement = models.BooleanField(default=False)
    parent_group = models.ForeignKey(
        'self',
        null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='remboursement_children'
    )

    class Meta:
        ordering = ['-date_creation']
        db_table = "epargnecredit_group"
        constraints = [
            UniqueConstraint(
                fields=['parent_group'],
                condition=Q(is_remboursement=True),
                name='unique_one_remboursement_per_parent_ec',
            ),
        ]
        indexes = [
            models.Index(fields=['is_remboursement']),
            models.Index(fields=['admin']),
        ]

    def __str__(self):
        suffix = " (remboursement)" if self.is_remboursement else ""
        return f"{self.nom}{suffix}"


# =========================================================
# MEMBRE
# =========================================================

class GroupMember(models.Model):

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='members_ec'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='groupmembers_ec'
    )

    alias = models.CharField(max_length=100, blank=True, null=True)
    montant = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    actif = models.BooleanField(default=True)
    exit_liste = models.BooleanField(default=False)

    date_ajout = models.DateTimeField(auto_now_add=True)
    date_joined = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "epargnecredit_groupmember"
        unique_together = ('group', 'user')

    def __str__(self):
        return f"{self.user} - {self.group.nom}"


# =========================================================
# VERSEMENT (CAISSE UNIQUEMENT)
# =========================================================

class Versement(models.Model):

    STATUT_CHOICES = (
        ("EN_ATTENTE", "En attente"),
        ("VALIDE", "Validé"),
        ("REFUSE", "Refusé"),
    )

    member = models.ForeignKey(
        GroupMember,
        on_delete=models.CASCADE,
        related_name='versements_ec'
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
        related_name="versements_valides_ec"
    )

    # 🔥 NOUVEAU : Numéro de reçu unique
    numero_recu = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True
    )

    date_creation = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(null=True, blank=True)

    transaction_id = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "epargnecredit_versement"
        ordering = ["-date_creation"]
        indexes = [
            models.Index(fields=["statut"]),
            models.Index(fields=["methode"]),
            models.Index(fields=["numero_recu"]),
        ]

    def __str__(self):
        return f"{self.member.user} - {self.montant} FCFA ({self.statut})"

    @property
    def montant_total(self):
        return self.montant + self.frais

    # =====================================================
    # GENERATION AUTOMATIQUE NUMERO RECU
    # =====================================================

    def generer_numero_recu(self):
        """
        Format :
        YESS-20260224-000123
        """
        if not self.numero_recu and self.id:
            date_str = timezone.now().strftime("%Y%m%d")
            self.numero_recu = f"YESS-{date_str}-{self.id:06d}"
            self.save(update_fields=["numero_recu"])

    # =====================================================
    # VALIDATION PROPRE
    # =====================================================

    def valider(self, admin_user):
        """
        Méthode centralisée pour valider un versement.
        """
        if self.statut != "VALIDE":
            self.statut = "VALIDE"
            self.valide_par = admin_user
            self.date_validation = timezone.now()
            self.save()
            self.generer_numero_recu()

    def refuser(self, admin_user):
        if self.statut != "REFUSE":
            self.statut = "REFUSE"
            self.valide_par = admin_user
            self.date_validation = timezone.now()
            self.save()


# =========================================================
# LOG GENERAL
# =========================================================

class ActionLog(models.Model):

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="action_logs_ec",
        null=True, blank=True
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="actionlogs_ec"
    )

    action = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        db_table = "epargnecredit_actionlog"

    def __str__(self):
        return f"{self.date} - {self.user}"


# =========================================================
# INVITATION
# =========================================================

class Invitation(models.Model):

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="invitations_ec")
    phone = models.CharField(max_length=20)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "epargnecredit_invitation"

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(days=7)

    def __str__(self):
        return f"Invitation {self.phone} - {self.group.nom}"


# =========================================================
# DEMANDE DE PRET
# =========================================================

class PretDemande(models.Model):

    STATUTS = (
        ("PENDING", "En attente"),
        ("APPROVED", "Approuvé"),
        ("REJECTED", "Refusé"),
    )

    member = models.ForeignKey(
        GroupMember,
        on_delete=models.CASCADE,
        related_name="demandes_pret_ec",
    )

    montant = models.DecimalField(max_digits=12, decimal_places=0)
    interet = models.DecimalField(max_digits=5, decimal_places=2)
    nb_mois = models.PositiveIntegerField()
    debut_remboursement = models.DateField()

    statut = models.CharField(max_length=10, choices=STATUTS, default="PENDING")
    commentaire = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="prets_decides_ec"
    )

    class Meta:
        db_table = "epargnecredit_pretdemande"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["member"],
                condition=models.Q(statut="PENDING"),
                name="uniq_pending_pret_par_membre_ec",
            )
        ]

    def __str__(self):
        return f"Demande prêt {self.member.user} - {self.montant} FCFA"

    @property
    def total_a_rembourser(self):
        return self.montant + (self.montant * (self.interet / 100))

    @property
    def mensualite(self):
        return (self.total_a_rembourser / self.nb_mois) if self.nb_mois else self.total_a_rembourser


