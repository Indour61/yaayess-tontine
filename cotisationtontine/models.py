from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import uuid


# =====================================================
# GROUPE TONTINE
# =====================================================

import uuid
from django.conf import settings
from django.db import models


class Group(models.Model):

    # -----------------------------
    # INFOS DE BASE
    # -----------------------------
    nom = models.CharField(max_length=255)

    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="groupes_administres_tontine"
    )

    group_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # -----------------------------
    # DATES
    # -----------------------------
    date_creation = models.DateTimeField(auto_now_add=True)
    date_reset = models.DateTimeField(null=True, blank=True)

    # -----------------------------
    # INVITATION
    # -----------------------------
    code_invitation = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    invitation_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # -----------------------------
    # MONTANTS
    # -----------------------------
    montant_base = models.DecimalField(max_digits=12, decimal_places=0, default=0)

    montant_fixe_gagnant = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        null=True,
        blank=True
    )

    # -----------------------------
    # GESTION DU CYCLE 🔥
    # -----------------------------
    cycle_numero = models.IntegerField(default=1)
    tour_actuel = models.IntegerField(default=1)

    is_active = models.BooleanField(default=True)
    cycle_termine = models.BooleanField(default=False)

    # -----------------------------
    # SUIVI DU GAGNANT
    # -----------------------------
    prochain_gagnant = models.ForeignKey(
        'GroupMember',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="groupes_prochain_gagnant"
    )

    # -----------------------------
    # CONFIGURATION
    # -----------------------------
    auto_reset = models.BooleanField(default=True)
    autoriser_ajout_membre = models.BooleanField(default=True)

    # -----------------------------
    # META
    # -----------------------------
    class Meta:
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.nom} (Cycle {self.cycle_numero} - Tour {self.tour_actuel})"

    # =====================================================
    # 🔥 MÉTHODES MÉTIER (ICI EN BAS ✅)
    # =====================================================

    def reset_apres_tirage(self):
        """
        🔥 Après chaque tirage :
        - passe au tour suivant
        """

        self.tour_actuel += 1
        self.is_active = True
        self.cycle_termine = False
        self.prochain_gagnant = None

        self.save()

    def total_membres(self):
        return self.membres.count()

    def total_cotise(self):
        """
        🔥 CORRECTION : basé sur Versement + tour
        """
        from .models import Versement
        from django.db.models import Sum

        return (
            Versement.objects
            .filter(
                member__group=self,
                statut="VALIDE",
                tour=self.tour_actuel
            )
            .aggregate(total=Sum("montant"))["total"] or 0
        )

    def cycle_est_termine(self):
        membres = self.membres.filter(actif=True, exit_liste=False)
        return all(m.a_recu for m in membres)

    def peut_cotiser(self):
        return self.is_active and not self.cycle_termine

# =====================================================
# 🔁 RESET COMPLET DU CYCLE
# =====================================================
def reset_cycle(self):
    """
    🔥 Reset complet :
    - remet les membres à zéro
    - réinitialise les tours
    - relance un nouveau cycle propre
    """

    membres = self.groupmember_set.all()

    for membre in membres:
        membre.montant = 0

        # 🔥 Sécurité
        if hasattr(membre, 'a_recu'):
            membre.a_recu = False

        membre.save()

    # 🔁 Nouveau cycle
    self.cycle_numero += 1

    # 🔥 TRÈS IMPORTANT
    self.tour_actuel = 1
    self.prochain_gagnant = None

    # 🔥 Réactivation propre
    self.cycle_termine = False
    self.is_active = True

    from django.utils import timezone
    self.date_reset = timezone.now()

    self.save()


# =====================================================
# 🔒 FIN DU CYCLE
# =====================================================
def verifier_et_cloturer_cycle(self):
    """
    Vérifie si tous les membres ont reçu leur tour
    et déclenche le reset si activé
    """

    # 🔒 Sécurité : éviter double exécution
    if self.cycle_termine:
        return

    membres_actifs = self.groupmember_set.filter(actif=True, exit_liste=False)

    if not membres_actifs.exists():
        return  # rien à faire

    # 🔍 Vérifie si tous ont reçu
    tous_ont_recu = all(
        getattr(m, "a_recu", False) for m in membres_actifs
    )

    if tous_ont_recu:

        # 🔒 Clôturer cycle
        self.cycle_termine = True
        self.is_active = False
        self.prochain_gagnant = None
        self.save()

        # 🔁 Reset automatique si activé
        if self.auto_reset:
            self.reset_cycle()

# =====================================================
# MEMBRE
# =====================================================

from django.conf import settings
from django.db import models
from django.utils import timezone


class GroupMember(models.Model):

    group = models.ForeignKey(
        'Group',
        on_delete=models.CASCADE,
        related_name='membres'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    alias = models.CharField(max_length=100, blank=True, null=True)

    # 💰 montant cotisé dans le cycle en cours
    montant = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0
    )

    # 🔥 NOUVEAU : suivi du cycle
    a_recu = models.BooleanField(
        default=False,
        help_text="Indique si ce membre a déjà reçu la cagnotte dans ce cycle"
    )

    ordre_passage = models.IntegerField(
        null=True,
        blank=True,
        help_text="Ordre de passage dans la tontine (optionnel)"
    )

    # -----------------------------
    # STATUT
    # -----------------------------
    actif = models.BooleanField(default=True)
    exit_liste = models.BooleanField(default=False)

    # -----------------------------
    # DATES
    # -----------------------------
    date_ajout = models.DateTimeField(auto_now_add=True)
    date_joined = models.DateTimeField(default=timezone.now)

    # -----------------------------
    # META
    # -----------------------------
    class Meta:
        unique_together = ('group', 'user')
        ordering = ['date_ajout']

    # -----------------------------
    # STRING
    # -----------------------------
    def __str__(self):
        return f"{self.get_display_name()} - {self.group.nom}"

    # =====================================================
    # MÉTHODES UTILES 🔥
    # =====================================================

    def get_display_name(self):
        """
        Retourne alias ou nom utilisateur
        """
        return self.alias if self.alias else getattr(self.user, "nom", str(self.user))

    def peut_cotiser(self):
        """
        Vérifie si le membre peut cotiser
        """
        return (
            self.actif
            and not self.exit_liste
            and self.group.is_active
            and not self.group.cycle_termine
        )

    def reset_pour_nouveau_cycle(self):
        """
        Reset du membre pour un nouveau cycle
        """
        self.montant = 0
        self.a_recu = False
        self.save()

from decimal import Decimal
from django.db import models
from django.conf import settings


from decimal import Decimal
from django.conf import settings
from django.db import models


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

    # 🔥 NOUVEAU : gestion des tours
    tour = models.IntegerField(
        default=1,
        help_text="Numéro du tour de tontine"
    )

    montant = models.DecimalField(max_digits=12, decimal_places=0)

    frais = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=Decimal("0")
    )

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
        indexes = [
            models.Index(fields=["member", "tour"]),
            models.Index(fields=["statut"]),
        ]

    def __str__(self):
        return f"{self.member.user} - {self.montant} FCFA (Tour {self.tour}) [{self.statut}]"

    # =====================================================
    # 🔹 Calcul automatique des frais YaayESS (2%)
    # =====================================================
    def save(self, *args, **kwargs):

        if not self.frais or self.frais == 0:
            self.frais = (self.montant * Decimal("0.02")).quantize(Decimal("1"))

        # 🔥 SÉCURITÉ : affecter automatiquement le tour si absent
        if not self.tour and self.member and self.member.group:
            self.tour = self.member.group.tour_actuel

        super().save(*args, **kwargs)

    # =====================================================
    # 💰 MONTANT TOTAL (avec frais)
    # =====================================================
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

    # 🔥 AJOUT CRUCIAL (OBLIGATOIRE)
    tour = models.PositiveIntegerField(
        default=1,
        help_text="Numéro du tour dans le cycle"
    )

    date_tirage = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_tirage"]
        indexes = [
            models.Index(fields=["group", "cycle_number", "tour"]),
        ]

    def __str__(self):
        return f"{self.group.nom} | Cycle {self.cycle_number} | Tour {self.tour}"


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


class Cycle(models.Model):
    group = models.ForeignKey("Group", on_delete=models.CASCADE, related_name="cycles")
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()

    def __str__(self):
        return f"Cycle {self.id} - {self.group.nom}"

    @property
    def total_etapes(self):
        return self.etapes.count()

    @property
    def completed_etapes(self):
        return self.etapes.filter(tirage__isnull=False).count()

    @property
    def progression(self):
        if self.total_etapes == 0:
            return 0
        return int((self.completed_etapes / self.total_etapes) * 100)


class EtapeCycle(models.Model):
    cycle = models.ForeignKey(Cycle, on_delete=models.CASCADE, related_name="etapes")
    numero_etape = models.IntegerField()
    date_etape = models.DateTimeField()

    tirage = models.ForeignKey(
        "Tirage",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Étape {self.numero_etape} - Cycle {self.cycle.id}"



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




