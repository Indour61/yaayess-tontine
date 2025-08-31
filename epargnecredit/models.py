from django.db import models
from django.conf import settings
import uuid
from django.utils import timezone


# ✅ Groupe principal
class Group(models.Model):
    nom = models.CharField(max_length=255, verbose_name="Nom du groupe")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_reset = models.DateTimeField(null=True, blank=True)
    code_invitation = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    invitation_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="groupes_administres_ec",
        verbose_name="Administrateur"
    )

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Code d'invitation")
    montant_base = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Montant de base")

    montant_fixe_gagnant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Montant fixe pour les gagnants"
    )

    prochain_gagnant = models.ForeignKey(
        'GroupMember',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="groupes_prochain_gagnant_ec",
        verbose_name="Prochain gagnant à exclure"
    )

    # ✅ Ajout de la relation ManyToMany via GroupMember
    membres_ec = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='GroupMember',
        related_name='groupes_ec',
        verbose_name="Membres"
    )

    class Meta:
        ordering = ['-date_creation']
        verbose_name = "Groupe"
        verbose_name_plural = "Groupes"
        db_table = "epargnecredit_group"

    def __str__(self):
        return f"{self.nom} (admin : {self.admin})"


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
