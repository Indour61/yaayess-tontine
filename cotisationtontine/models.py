from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

class Group(models.Model):
    nom = models.CharField(max_length=255, verbose_name="Nom du groupe")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_reset = models.DateTimeField(null=True, blank=True)
    code_invitation = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)  # 👈 Nouveau champ
    invitation_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="groupes_administres",
        verbose_name="Administrateur"
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Code d'invitation")
    montant_base = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Montant de base")

    class Meta:
        ordering = ['-date_creation']
        verbose_name = "Groupe"
        verbose_name_plural = "Groupes"

    def __str__(self):
        return f"{self.nom} (admin : {self.admin})"

# ✅ Membre du groupe
class GroupMember(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='membres')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    montant = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Montant épargné
    actif = models.BooleanField(default=True)
    exit_liste = models.BooleanField(default=False)  # Exclu du tirage
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('group', 'user')
        verbose_name = "Membre du groupe"
        verbose_name_plural = "Membres du groupe"

    def __str__(self):
        return f"{self.user.nom}"

# ✅ Historique des tirages
class TirageHistorique(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='tirages_historiques')
    gagnant = models.ForeignKey(GroupMember, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Gagnant")
    montant = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    date_tirage = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Tirage {self.date_tirage.strftime('%d/%m/%Y')} - {self.gagnant} - {self.montant} FCFA"

# ✅ Cotisation par membre (versement dans le cycle)
class CotisationTontine(models.Model):
    member = models.ForeignKey(GroupMember, on_delete=models.CASCADE, related_name='cotisations')
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

    def __str__(self):
        return f"{self.member.user.nom} - {self.montant} FCFA - {self.get_statut_display()}"


from django.db import models
#from .group import Group
#from .groupmember import GroupMember

class Tirage(models.Model):
    """
    Représente un tirage au sort dans un groupe de tontine.
    Chaque tirage est lié à un groupe, un gagnant, et un membre participant.
    """
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="tirages",  # ✅ Ajout du related_name pour accéder via group.tirages.all()
        verbose_name="Groupe"
    )

    date_tirage = models.DateField(
        auto_now_add=True,
        verbose_name="Date du tirage"
    )

    montant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Montant du tirage"
    )

    gagnant = models.ForeignKey(
        GroupMember,
        on_delete=models.CASCADE,
        related_name="tirages_gagnes",
        verbose_name="Membre gagnant"
    )

    membre = models.ForeignKey(
        GroupMember,
        on_delete=models.CASCADE,
        related_name="tirages_participes",
        verbose_name="Membre tiré"
    )

    def __str__(self):
        return f"Tirage {self.date_tirage} - {self.group.nom}"

# ✅ Invitation pour rejoindre un groupe
class Invitation(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='invitations')
    phone = models.CharField(max_length=50)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    expire_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    def est_valide(self):
        return timezone.now() < self.expire_at and not self.used

    def __str__(self):
        return f"Invitation {self.phone} pour {self.group.nom}"

from django.db import models
from django.conf import settings
#from cotisationtontine.models import GroupMember  # 🛠️ Assure-toi que le chemin est correct

# ✅ Versement d’un membre
class Versement(models.Model):
    METHODE_CHOICES = [
        ('PAYDUNYA', 'PayDunya'),
        ('CASH', 'Caisse'),
    ]

    member = models.ForeignKey(
        GroupMember,
        on_delete=models.CASCADE,
        related_name='versements'
    )
    montant = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Montant net du versement (hors frais)."
    )
    frais = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Frais appliqués sur le paiement."
    )
    date = models.DateTimeField(auto_now_add=True)

    methode = models.CharField(
        max_length=50,
        choices=METHODE_CHOICES,
        default='PAYDUNYA'
    )
    transaction_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    def __str__(self):
        return f"Versement {self.montant} FCFA (+{self.frais} FCFA frais) par {self.member.user.nom}"

    @property
    def montant_total(self):
        """Montant total payé = montant + frais (utile pour PayDunya)."""
        return self.montant + self.frais

# ✅ Historique des actions générales
class ActionLog(models.Model):
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="action_logs",  # <- NOM CHANGÉ
        null=True,
        blank=True
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} - {self.user} : {self.action}"


# ✅ Historique spécifique (avec types d'actions prédéfinis)
class HistoriqueAction(models.Model):
    ACTION_CHOICES = [
        ('RESET_CYCLE', 'Réinitialisation du cycle'),
        ('AUTRE', 'Autre action'),
    ]

    group = models.ForeignKey(
        'Group',
        on_delete=models.CASCADE,
        related_name='historique_actions'  # <- NOM CHANGÉ
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.get_action_display()} - {self.group.nom} - {self.date.strftime('%d/%m/%Y %H:%M')}"


# tontine/models.py
from django.db import models
from django.conf import settings
from .models import Group, GroupMember  # Assure-toi que c’est bien dans le même fichier

class PaiementGagnant(models.Model):
    STATUT_CHOICES = [
        ('SUCCES', 'Succès'),
        ('ECHEC', 'Échec'),
    ]

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="paiements")
    gagnant = models.ForeignKey(GroupMember, on_delete=models.CASCADE, related_name="paiements_reçus")
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES)
    message = models.TextField(blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    date_paiement = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_paiement']
        verbose_name = "Paiement gagnant"
        verbose_name_plural = "Paiements des gagnants"

    def __str__(self):
        return f"{self.gagnant.user.nom} - {self.montant} FCFA - {self.statut}"

