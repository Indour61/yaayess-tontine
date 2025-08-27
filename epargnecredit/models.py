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


# ✅ Historique des tirages
class TirageHistorique(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='tirages_historiques_ec')
    gagnant = models.ForeignKey(GroupMember, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Gagnant")
    montant = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    date_tirage = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "epargnecredit_tirage_historique"

    def __str__(self):
        return f"Tirage {self.date_tirage.strftime('%d/%m/%Y')} - {self.gagnant} - {self.montant} FCFA"


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


# ✅ Tirage
class Tirage(models.Model):
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="tirages_ec",
        verbose_name="Groupe"
    )
    date_tirage = models.DateField(auto_now_add=True, verbose_name="Date du tirage")
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant du tirage")
    gagnant = models.ForeignKey(GroupMember, on_delete=models.CASCADE, related_name="tirages_gagnes_ec", verbose_name="Membre gagnant")
    membre = models.ForeignKey(GroupMember, on_delete=models.CASCADE, related_name="tirages_participes_ec", verbose_name="Membre tiré")

    class Meta:
        db_table = "epargnecredit_tirage"

    def __str__(self):
        return f"Tirage {self.date_tirage} - {self.group.nom}"


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


# ✅ Paiement gagnant
class PaiementGagnant(models.Model):
    STATUT_CHOICES = [
        ('SUCCES', 'Succès'),
        ('ECHEC', 'Échec'),
    ]
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="paiements_ec")
    gagnant = models.ForeignKey(GroupMember, on_delete=models.CASCADE, related_name="paiements_reçus_ec")
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES)
    message = models.TextField(blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    date_paiement = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_paiement']
        verbose_name = "Paiement gagnant"
        verbose_name_plural = "Paiements des gagnants"
        db_table = "epargnecredit_paiementgagnant"

    def __str__(self):
        return f"{self.gagnant.user} - {self.montant} FCFA - {self.statut}"


# ✅ Invitation
class Invitation(models.Model):
    group = models.ForeignKey('Group', on_delete=models.CASCADE, related_name="invitations_ec")
    phone = models.CharField(max_length=20)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expire_at = models.DateTimeField()

    class Meta:
        db_table = "epargnecredit_invitation"

    def is_expired(self):
        return timezone.now() > self.expire_at

    def __str__(self):
        return f"Invitation for {self.phone} to join {self.group.nom}"