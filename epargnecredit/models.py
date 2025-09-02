from django.db import models
from django.conf import settings
from django.db.models import Q, UniqueConstraint
import uuid


class Group(models.Model):
    # ✅ Infos de base
    nom = models.CharField(max_length=255, verbose_name="Nom du groupe")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_reset = models.DateTimeField(null=True, blank=True)

    # ✅ Invitations (tu as les deux : on conserve tel quel)
    code_invitation = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    invitation_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # ✅ Admin
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="groupes_administres_ec",
        verbose_name="Administrateur"
    )

    # ⚠️ Champ historique chez toi, libellé “Code d’invitation”
    # (on le garde pour compat descendante)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Code d'invitation")

    # ✅ Montants
    montant_base = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, verbose_name="Montant de base"
    )
    montant_fixe_gagnant = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Montant fixe pour les gagnants"
    )

    # ✅ Flux tontine (si tu l’utilises côté épargne&crédit)
    prochain_gagnant = models.ForeignKey(
        'GroupMember',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="groupes_prochain_gagnant_ec",
        verbose_name="Prochain gagnant à exclure"
    )

    # ✅ Relation membres via table pivot
    membres_ec = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='GroupMember',
        related_name='groupes_ec',
        verbose_name="Membres"
    )

    # 🆕 Spécifique “groupe remboursement”
    is_remboursement = models.BooleanField(
        default=False, help_text="Coché pour un groupe de remboursement"
    )
    parent_group = models.ForeignKey(
        'self',
        null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='remboursement_children',
        help_text="Si groupe de remboursement, lien vers le groupe parent"
    )

    class Meta:
        ordering = ['-date_creation']
        verbose_name = "Groupe"
        verbose_name_plural = "Groupes"
        db_table = "epargnecredit_group"
        constraints = [
            # ✅ Un seul groupe remboursement par parent (partial unique index)
            UniqueConstraint(
                fields=['parent_group', 'is_remboursement'],
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
        return f"{self.nom}{suffix} — admin: {self.admin}"

    # Helpers pratiques
    def has_remboursement_group(self) -> bool:
        return self.remboursement_children.filter(is_remboursement=True).exists()

    def get_remboursement_group(self):
        return self.remboursement_children.filter(is_remboursement=True).first()


from django.db import models
from django.conf import settings
from django.utils import timezone  # ✅ Import manquant

class GroupMember(models.Model):
    group = models.ForeignKey(
        'Group',
        on_delete=models.CASCADE,
        related_name='members',  # ⚡ Changer pour un nom unique
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='groupmembers_ec'
    )
    alias = models.CharField(max_length=100, blank=True, null=True)
    montant = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    actif = models.BooleanField(default=True)
    exit_liste = models.BooleanField(default=False)
    date_ajout = models.DateTimeField(auto_now_add=True)
    date_joined = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('group', 'user')
        db_table = "epargnecredit_groupmember"

    def __str__(self):
        return f"{self.user} - {self.group.nom}"


# ✅ Cotisation par membre
class EpargneCredit(models.Model):
    member = models.ForeignKey(GroupMember, on_delete=models.CASCADE, related_name='cotisations_ec')
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(
        max_length=20,
        choices=[
            ("VALIDE", "Validé"),
            ("EN_ATTENTE", "En attente"),
            ("REFUSE", "Refusé"),
        ],
        default="EN_ATTENTE"
    )

    class Meta:
        db_table = "epargnecredit_cotisation"

    def __str__(self):
        return f"{self.member.user} - {self.montant} FCFA - {self.get_statut_display()}"


# ✅ Versement
class Versement(models.Model):
    METHODE_CHOICES = [
        ('PAYDUNYA', 'PayDunya'),
        ('CASH', 'Caisse'),
    ]
    member = models.ForeignKey(GroupMember, on_delete=models.CASCADE, related_name='versements_ec')
    montant = models.DecimalField(max_digits=12, decimal_places=2, help_text="Montant net du versement (hors frais).")
    frais = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Frais appliqués sur le paiement.")
    date = models.DateTimeField(auto_now_add=True)
    methode = models.CharField(max_length=50, choices=METHODE_CHOICES, default='PAYDUNYA')
    transaction_id = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "epargnecredit_versement"

    def __str__(self):
        return f"Versement {self.montant} FCFA (+{self.frais} FCFA frais) par {self.member.user}"

    @property
    def montant_total(self):
        return self.montant + self.frais


# ✅ Historique des actions générales
class ActionLog(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="action_logs_ec", null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="actionlogs_ec"
    )
    action = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        db_table = "epargnecredit_actionlog"

    def __str__(self):
        return f"{self.date} - {self.user} : {self.action}"


# ✅ Historique spécifique
class HistoriqueAction(models.Model):
    ACTION_CHOICES = [
        ('RESET_CYCLE', 'Réinitialisation du cycle'),
        ('AUTRE', 'Autre action'),
    ]
    group = models.ForeignKey('Group', on_delete=models.CASCADE, related_name='historique_actions_ec')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    date = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "epargnecredit_historiqueaction"

    def __str__(self):
        return f"{self.get_action_display()} - {self.group.nom} - {self.date.strftime('%d/%m/%Y %H:%M')}"


# ✅ Invitation
import uuid
from django.db import models
from django.utils import timezone

class Invitation(models.Model):
    group = models.ForeignKey('Group', on_delete=models.CASCADE, related_name="invitations_ec")
    phone = models.CharField(max_length=20)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "epargnecredit_invitation"

    def is_expired(self):
        # Exemple : expiration automatique 7 jours après création
        return timezone.now() > self.created_at + timezone.timedelta(days=7)

    def __str__(self):
        return f"Invitation for {self.phone} to join {self.group.nom}"

# epargnecredit/models.py
from django.conf import settings
from django.db import models

class PretDemande(models.Model):
    STATUTS = (
        ("PENDING", "En attente"),
        ("APPROVED", "Approuvé"),
        ("REJECTED", "Refusé"),
    )

    member = models.ForeignKey(
        "GroupMember",
        on_delete=models.CASCADE,
        related_name="demandes_pret_ec",
    )
    montant = models.DecimalField(max_digits=12, decimal_places=0)
    interet = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="Pourcentage annuel simple, ex. 5 pour 5%"
    )
    nb_mois = models.PositiveIntegerField()
    debut_remboursement = models.DateField()

    statut = models.CharField(max_length=10, choices=STATUTS, default="PENDING")
    commentaire = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="prets_decides_ec"
    )

    class Meta:
        db_table = "epargnecredit_pretdemande"
        ordering = ["-created_at"]
        constraints = [
            # Un seul prêt "en attente" par membre
            models.UniqueConstraint(
                fields=["member"],
                condition=models.Q(statut="PENDING"),
                name="uniq_pending_pret_par_membre_ec",
            )
        ]

    def __str__(self):
        return f"Demande prêt {self.member.user} ({self.montant} FCFA) - {self.get_statut_display()}"

    @property
    def total_a_rembourser(self):
        # Intérêt simple global
        return self.montant + (self.montant * (self.interet / 100))

    @property
    def mensualite(self):
        return (self.total_a_rembourser / self.nb_mois) if self.nb_mois else self.total_a_rembourser
