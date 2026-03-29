from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from cotisationtontine.models import Group, GroupMember, Versement, ActionLog



from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Group, Versement, ActionLog


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

from .models import Group, Versement, ActionLog



@login_required
def dashboard_tontine_simple(request):
    """
    Dashboard principal Tontine
    Visible uniquement si l'utilisateur administre un groupe
    """

    user = request.user

    # =====================================================
    # 🔒 Sécurité : vérifier si utilisateur admin d'un groupe
    # =====================================================

    groupes_admin = (
        Group.objects
        .filter(admin=user)
        .prefetch_related("membres")
        .order_by("-date_creation")
    )

    if not groupes_admin.exists():
        messages.warning(
            request,
            "Vous n’êtes administrateur d’aucun groupe."
        )
#        return redirect("accounts:login")
        return render(
            request,
            "cotisationtontine/no_group.html"
        )
    # =====================================================
    # 👥 Groupes où l'utilisateur est membre
    # =====================================================

    groupes_membre = (
        Group.objects
        .filter(membres__user=user)
        .exclude(admin=user)
        .distinct()
    )

    # =====================================================
    # 📝 Dernières actions utilisateur
    # =====================================================

    dernieres_actions = (
        ActionLog.objects
        .filter(user=user)
        .select_related("group")
        .order_by("-date")[:10]
    )

    # =====================================================
    # 💰 Total versements utilisateur
    # =====================================================

    total_versements = (
        Versement.objects
        .filter(member__user=user, statut="VALIDE")
        .aggregate(total=Sum("montant"))
        .get("total") or 0
    )

    # =====================================================
    # 📊 Nombre total groupes utilisateur
    # =====================================================

    total_groupes = (
        Group.objects
        .filter(membres__user=user)
        .distinct()
        .count()
    )

    # =====================================================
    # 📅 Versements récents (30 jours)
    # =====================================================

    date_limite = timezone.now() - timedelta(days=30)

    versements_recents = (
        Versement.objects
        .filter(
            member__user=user,
            date_creation__gte=date_limite
        )
        .select_related("member__group")
        .order_by("-date_creation")[:5]
    )

    # =====================================================
    # 📈 Stats groupes administrés
    # =====================================================

    stats_groupes_admin = (
        Versement.objects
        .filter(member__group__admin=user, statut="VALIDE")
        .values(
            "member__group__id",
            "member__group__nom"
        )
        .annotate(
            versements_total=Sum("montant")
        )
        .order_by("-versements_total")
    )

    # =====================================================
    # 📦 Context
    # =====================================================

    context = {
        "groupes_admin": groupes_admin,
        "groupes_membre": groupes_membre,
        "action_logs": dernieres_actions,  # 🔥 CORRECTION ICI
        "total_versements": total_versements,
        "total_groupes": total_groupes,
        "versements_recents": versements_recents,
        "stats_groupes_admin": stats_groupes_admin,
    }

    return render(
        request,
        "cotisationtontine/dashboard.html",
        context
    )

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.db import transaction, IntegrityError
from django.db.models import Sum
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import requests
from decimal import Decimal

from cotisationtontine.forms import GroupForm, GroupMemberForm, VersementForm
from cotisationtontine.models import Group, GroupMember, Invitation, Versement, ActionLog
from accounts.models import CustomUser
from accounts.utils import envoyer_invitation


@login_required
@transaction.atomic
def ajouter_groupe_view(request):
    """
    Création d'un nouveau groupe par un utilisateur connecté :
    1️⃣ Création du groupe avec l'utilisateur comme admin
    2️⃣ Ajout de l'admin comme membre
    3️⃣ Génération d'un lien d'invitation
    4️⃣ Envoi de l'invitation (simulation WhatsApp ou SMS)
    """
    if request.method == "POST":
        form = GroupForm(request.POST)
        if form.is_valid():
            try:
                # ✅ Créer le groupe
                group = form.save(commit=False)
                group.admin = request.user
                group.save()

                # ✅ Ajoute l'admin comme membre du groupe
                GroupMember.objects.create(
                    group=group,
                    user=request.user,
                    montant=0
                )

                # ✅ Crée un lien d'invitation sécurisé (utilise le code_invitation du groupe)
                lien_invitation = request.build_absolute_uri(
                    reverse("accounts:inscription_et_rejoindre", args=[str(group.code_invitation)])
                )

                # ✅ Simule l'envoi de l'invitation (WhatsApp ou SMS)
                envoyer_invitation(request.user.phone, lien_invitation)

                # ✅ Message de confirmation
                messages.success(request,
                                 f"Groupe « {group.nom} » créé avec succès et vous avez été ajouté comme membre.")

                # ✅ Redirection vers le dashboard Tontine
                return redirect("cotisationtontine:dashboard_tontine_simple")

            except Exception as e:
                messages.error(request, f"Erreur lors de la création du groupe: {str(e)}")
    else:
        form = GroupForm()

    return render(
        request,
        "cotisationtontine/ajouter_groupe.html",
        {"form": form, "title": "Créer un groupe"}
    )

@login_required
@transaction.atomic
def ajouter_membre_view(request, group_id):
    """
    Ajouter un membre à un groupe existant.
    Seul l'administrateur du groupe peut ajouter des membres.
    """
    group = get_object_or_404(Group, id=group_id)

    # Vérification des droits : seul l'admin du groupe peut ajouter
    if group.admin != request.user:
        messages.error(request, "⚠️ Vous n'avez pas les droits pour ajouter un membre à ce groupe.")
        return redirect("cotisationtontine:dashboard_tontine_simple")

    if request.method == "POST":
        form = GroupMemberForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data.get("phone")
            nom = form.cleaned_data.get("nom")

            # Vérifier si un utilisateur existe déjà avec ce numéro
            user, created_user = CustomUser.objects.get_or_create(
                phone=phone,
                defaults={"nom": nom or f"Utilisateur {phone}"}
            )

            # Si le user existait déjà mais avec un autre nom → prévenir
            if not created_user and user.nom != nom:
                messages.warning(
                    request,
                    f"⚠️ Ce numéro est déjà associé à {user.nom}. Le nom fourni ({nom}) a été ignoré."
                )
                nom = user.nom  # Utiliser le nom existant

            # Vérifier si le membre est déjà dans ce groupe
            if GroupMember.objects.filter(group=group, user=user).exists():
                messages.info(request, f"ℹ️ {user.nom} est déjà membre du groupe {group.nom}.")
                return redirect("cotisationtontine:group_detail", group_id=group.id)

            # ✅ Vérifier si le nom existe déjà dans ce groupe avec un autre numéro
            existing_members_same_name = GroupMember.objects.filter(group=group, user__nom=nom).exclude(user__phone=phone)
            alias = None
            if existing_members_same_name.exists():
                # ✅ Message explicite avant l'ajout
                messages.warning(
                    request,
                    f"⚠️ Le nom '{nom}' existe déjà dans le groupe avec un autre numéro. "
                    f"Un alias sera créé pour éviter la confusion."
                )
                alias = f"{nom} ({phone})"

            # Ajouter le membre
            group_member = GroupMember.objects.create(
                group=group,
                user=user,
                montant=0,
                alias=alias
            )

            # Message de confirmation
            if alias:
                messages.success(request, f"✅ {alias} a été ajouté au groupe {group.nom}.")
            else:
                messages.success(request, f"✅ {user.nom} a été ajouté au groupe {group.nom}.")

            # TODO: Simuler envoi WhatsApp
            # message = f"Bonjour {user.nom}, vous avez été ajouté au groupe {group.nom} sur YaayESS. Connectez-vous avec votre numéro {phone}."
            # simulate_whatsapp_send(phone, message)

            return redirect("cotisationtontine:group_detail", group_id=group.id)
    else:
        form = GroupMemberForm()

    return render(request, "cotisationtontine/ajouter_membre.html", {
        "group": group,
        "form": form
    })

from django.db.models import Q  # Ajoutez cette importation en haut du fichier

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Q
from cotisationtontine.models import Group


@login_required
def group_list_view(request):
    """
    Liste des groupes de l'utilisateur
    """

    user = request.user

    # 🔑 Super admin : voir tous les groupes
    if getattr(user, "is_super_admin", False):
        groupes = Group.objects.all().order_by("-date_creation")

    else:
        groupes = (
            Group.objects.filter(
                Q(admin=user) |
                Q(membres__user=user)
            )
            .distinct()
            .order_by("-date_creation")
        )

    context = {
        "groupes": groupes
    }

    return render(
        request,
        "cotisationtontine/group_list.html",
        context
    )

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db.models import Sum, Q, Value, DecimalField, OuterRef, Subquery
from django.db.models.functions import Coalesce

from .models import Group, GroupMember, Versement, ActionLog


# =====================================================
# 📊 Dashboard simple
# =====================================================

@login_required
def dashboard(request):

    action_logs = (
        ActionLog.objects
        .filter(user=request.user)
        .order_by("-date")[:10]
    )

    context = {
        "action_logs": action_logs
    }

    return render(
        request,
        "cotisationtontine/dashboard.html",
        context
    )


# =====================================================
# 👥 Détail d’un groupe
# =====================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse

from django.db.models import Q, Sum, Value, DecimalField, Subquery, OuterRef
from django.db.models.functions import Coalesce

from accounts.models import Notification

from .models import Group, GroupMember, Versement, ActionLog


@login_required
def group_detail(request, group_id):

    group = get_object_or_404(Group, id=group_id)

    # -------------------------------------------------
    # 🔔 NOTIFICATIONS
    # -------------------------------------------------
    notifications = Notification.objects.order_by('-created_at')[:5]

    # -------------------------------------------------
    # 🔒 Vérification accès utilisateur
    # -------------------------------------------------
    has_access = (
        group.admin_id == request.user.id
        or GroupMember.objects.filter(group=group, user=request.user).exists()
        or getattr(request.user, "is_super_admin", False)
        or request.user.is_superuser
    )

    if not has_access:
        messages.error(request, "⚠️ Vous n'avez pas accès à ce groupe.")
        return redirect("cotisationtontine:dashboard_tontine_simple")

    # -------------------------------------------------
    # 👑 Vérifier si admin
    # -------------------------------------------------
    user_is_admin = (
        request.user == group.admin
        or getattr(request.user, "is_super_admin", False)
        or request.user.is_superuser
    )

    # -------------------------------------------------
    # 💳 Versements en attente (admin seulement)
    # -------------------------------------------------
    versements_en_attente_liste = []

    if user_is_admin:
        versements_en_attente_liste = (
            Versement.objects
            .filter(member__group=group, statut="EN_ATTENTE")
            .select_related("member__user")
            .order_by("-date_creation")
        )

    # -------------------------------------------------
    # 📊 Calcul versements membres
    # -------------------------------------------------
    rel_lookup = "versements"

    last_qs = Versement.objects.filter(
        member=OuterRef("pk"),
        statut="VALIDE"
    )

    if group.date_reset:
        last_qs = last_qs.filter(date_creation__gte=group.date_reset)

    last_qs = last_qs.order_by("-date_creation")

    sum_filter = Q(**{f"{rel_lookup}__statut": "VALIDE"})

    if group.date_reset:
        sum_filter &= Q(**{f"{rel_lookup}__date_creation__gte": group.date_reset})

    membres = (
        GroupMember.objects
        .filter(group=group)
        .select_related("user")
        .annotate(
            total_montant=Coalesce(
                Sum(f"{rel_lookup}__montant", filter=sum_filter),
                Value(0, output_field=DecimalField(max_digits=12, decimal_places=2)),
            ),
            last_amount=Subquery(last_qs.values("montant")[:1]),
            last_date=Subquery(last_qs.values("date_creation")[:1]),
        )
        .order_by("id")
    )

    # -------------------------------------------------
    # 🔄 Associer versement en attente à chaque membre
    # -------------------------------------------------
    versements_map = {}

    if user_is_admin:
        versements = (
            Versement.objects
            .filter(member__group=group, statut="EN_ATTENTE")
            .select_related("member")
            .order_by("-date_creation")
        )

        for v in versements:
            if v.member_id not in versements_map:
                versements_map[v.member_id] = v

    for m in membres:
        m.versement_en_attente = versements_map.get(m.id)

    # -------------------------------------------------
    # 💰 Total global du groupe
    # -------------------------------------------------
    total_filter = Q(member__group=group, statut="VALIDE")

    if group.date_reset:
        total_filter &= Q(date_creation__gte=group.date_reset)

    total_montant = (
        Versement.objects
        .filter(total_filter)
        .aggregate(
            total=Coalesce(
                Sum("montant"),
                Value(0, output_field=DecimalField(max_digits=12, decimal_places=2)),
            )
        )["total"]
    )

    # -------------------------------------------------
    # 📝 Historique actions
    # -------------------------------------------------
    actions = (
        ActionLog.objects
        .filter(group=group)
        .select_related("user")
        .order_by("-date")[:10]
    )

    # -------------------------------------------------
    # 🔗 Lien invitation
    # -------------------------------------------------
    code = None

    for field in ("code_invitation", "invitation_token", "uuid"):
        if hasattr(group, field) and getattr(group, field):
            code = str(getattr(group, field))
            break

    invite_arg = code if code else str(group.id)

    invite_url = request.build_absolute_uri(
        reverse("accounts:inscription_et_rejoindre", args=[invite_arg])
    )

    if user_is_admin:
        request.session["last_invitation_link"] = invite_url

    # -------------------------------------------------
    # 🎲 ÉTAT DU CYCLE (tirage)
    # -------------------------------------------------

    # 🔁 Détection cycle actuel
    dernier_tirage = group.tirages.order_by("-date_tirage").first()
    cycle_actuel = dernier_tirage.cycle_number if dernier_tirage else 1

    # 👥 membres actifs uniquement
    membres_actifs = group.membres.filter(actif=True, exit_liste=False)

    # 🏆 gagnants du cycle actuel
    gagnants_ids = group.tirages.filter(
        cycle_number=cycle_actuel
    ).values_list("gagnant_id", flat=True)

    # 👤 membres restants
    membres_restants = membres_actifs.exclude(id__in=gagnants_ids)

    # ✅ état final
    cycle_termine = not membres_restants.exists()

    # 📊 infos utiles UI
    nb_restants = membres_restants.count()
    total_membres = membres_actifs.count()
    nb_termines = total_membres - nb_restants

    progress = int((nb_termines / total_membres) * 100) if total_membres > 0 else 0



    # -------------------------------------------------
    # 📦 CONTEXT FINAL
    # -------------------------------------------------
    context = {
        "group": group,
        "membres": membres,
        "total_montant": total_montant,
        "admin_user": group.admin,
        "actions": actions,
        "user_is_admin": user_is_admin,
        "invite_url": invite_url,
        "last_invitation_link": request.session.get("last_invitation_link"),
        "versements_en_attente_liste": versements_en_attente_liste,
        "notifications": notifications,

        # 🎲 AJOUT ICI
        "cycle_termine": cycle_termine,
        "cycle_actuel": cycle_actuel,
        "nb_restants": nb_restants,
        "progress": progress,
    }


    return render(
        request,
        "cotisationtontine/group_detail.html",
        context
    )


# views.py
import os
import json
from decimal import Decimal, ROUND_HALF_UP
import requests

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

#from .models import GroupMember, Versement


from decimal import Decimal, ROUND_HALF_UP
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

# ==========================================
# DECLARATION VERSEMENT CAISSE
# ==========================================
from decimal import Decimal, ROUND_HALF_UP
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib import messages

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.db.models import Sum
from decimal import Decimal, ROUND_HALF_UP

@login_required
@transaction.atomic
def initier_versement(request, member_id):

    member = get_object_or_404(
        GroupMember.objects.select_related("group", "user"),
        id=member_id
    )

    group = member.group

    # 🔒 RÈGLE MÉTIER (sécurité)
    user_is_admin = (
        request.user == group.admin
        or request.user.is_superuser
    )

    if not user_is_admin and request.user != member.user:
        messages.error(request, "❌ Vous ne pouvez verser que pour vous-même.")
        return redirect("cotisationtontine:group_detail", group_id=group.id)

    # =============================
    # 📊 TOTAL ACTUEL
    # =============================
    total_actuel = member.versements.filter(
        statut__in=["EN_ATTENTE", "VALIDE"]
    ).aggregate(total=Sum("montant"))["total"] or Decimal("0")

    montant_max = group.montant_base or Decimal("0")

    reste = montant_max - total_actuel

    # =============================
    # FORMULAIRE GET
    # =============================
    if request.method == "GET":

        frais = (reste * Decimal("0.02")).quantize(Decimal("1"))
        total = reste + frais

        return render(
            request,
            "cotisationtontine/initier_versement.html",
            {
                "member": member,
                "group": group,
                "montant_base": montant_max,
                "reste": reste,
                "frais": frais,
                "total": total
            }
        )

    # =============================
    # TRAITEMENT POST
    # =============================
    montant_raw = (request.POST.get("montant") or "").replace(",", ".").strip()

    try:
        montant = Decimal(montant_raw)
    except Exception:
        messages.error(request, "❌ Montant invalide.")
        return redirect("cotisationtontine:initier_versement", member_id=member_id)

    if montant <= 0:
        messages.error(request, "❌ Le montant doit être supérieur à 0.")
        return redirect("cotisationtontine:initier_versement", member_id=member_id)

    montant = montant.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    # =============================
    # 🔒 BLOQUER SI DÉJÀ PAYÉ
    # =============================
    if reste <= 0:
        messages.warning(request, "✅ Vous avez déjà atteint le montant requis.")
        return redirect("cotisationtontine:group_detail", group_id=group.id)

    # =============================
    # 🔒 BLOQUER DÉPASSEMENT
    # =============================
    if montant > reste:
        messages.error(
            request,
            f"❌ Dépassement interdit ! Il vous reste seulement {reste} FCFA à payer."
        )
        return redirect("cotisationtontine:initier_versement", member_id=member_id)

    # =============================
    # 💰 CALCUL FRAIS
    # =============================
    frais = (montant * Decimal("0.02")).quantize(Decimal("1"))

    # =============================
    # 💾 ENREGISTREMENT
    # =============================
    Versement.objects.create(
        member=member,
        montant=montant,
        frais=frais,
        methode="CAISSE",
        statut="EN_ATTENTE"
    )

    messages.success(
        request,
        f"✅ Versement de {montant} FCFA enregistré pour {member.user.nom or member.user.phone}. En attente de validation."
    )

    return redirect("cotisationtontine:group_detail", group_id=group.id)

# ==========================================
# VALIDATION ADMIN
# ==========================================

@login_required
@transaction.atomic
def valider_versement(request, versement_id):

    versement = get_object_or_404(
        Versement.objects.select_related("member__group"),
        id=versement_id
    )
    group = versement.member.group

    if request.user != group.admin and not request.user.is_superuser:
        messages.error(request, "Accès refusé.")
        return redirect("cotisationtontine:group_detail", group_id=group.id)

    versement.statut = "VALIDE"
    versement.valide_par = request.user
    versement.date_validation = timezone.now()
    versement.save()

    messages.success(request, "Versement validé avec succès.")
    return redirect("cotisationtontine:group_detail", group_id=group.id)


# ==========================================
# REFUSER VERSEMENT
# ==========================================

@login_required
@transaction.atomic
def refuser_versement(request, versement_id):

    versement = get_object_or_404(
        Versement.objects.select_related("member__group"),
        id=versement_id
    )
    group = versement.member.group

    if request.user != group.admin and not request.user.is_superuser:
        messages.error(request, "Accès refusé.")
        return redirect("cotisationtontine:group_detail", group_id=group.id)

    versement.statut = "REFUSE"
    versement.valide_par = request.user
    versement.date_validation = timezone.now()
    versement.save()

    messages.success(request, "Versement refusé.")
    return redirect("cotisationtontine:group_detail", group_id=group.id)


def editer_membre_view(request, group_id, membre_id):
    return HttpResponse(f"Éditer membre {membre_id} du groupe {group_id}")

def supprimer_membre_view(request, group_id, membre_id):
    return HttpResponse(f"Supprimer membre {membre_id} du groupe {group_id}")


def reset_cycle_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    # Ici tu réinitialises les versements/crédits selon ta logique
    messages.info(request, f"Cycle réinitialisé pour le groupe {group.nom} (à implémenter).")
    return redirect("cotisationtontine:group_detail", group_id=group.id)

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
import random

from cotisationtontine.models import Group, Tirage, Versement

from django.db.models import Sum

import random
from django.db.models import Sum, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction

@login_required
@transaction.atomic
def tirage_au_sort_view(request, group_id):

    group = get_object_or_404(Group, id=group_id)

    # 🔒 Sécurité
    if request.user != group.admin and not request.user.is_superuser:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"error": "Accès non autorisé"}, status=403)

        messages.error(request, "Accès non autorisé.")
        return redirect("cotisationtontine:group_detail", group_id=group.id)

    membres_actifs = group.membres.filter(actif=True, exit_liste=False)

    # 🔒 Vérifier que tous les membres ont payé (cotisation du cycle)

    # 🔒 Vérifier que tous les membres ont payé (cotisation du cycle)

    from .models import Versement

    filter_q = Q(member__group=group, statut="VALIDE")

    # 🔄 gérer reset
    if group.date_reset:
        filter_q &= Q(date_creation__gte=group.date_reset)

    membres_non_a_jour = []

    for membre in membres_actifs:
        a_paye = Versement.objects.filter(
            filter_q,
            member=membre
        ).exists()

        if not a_paye:
            membres_non_a_jour.append(
                membre.alias or getattr(membre.user, "username", "Membre")
            )

    if membres_non_a_jour:
        return JsonResponse({
            "error": "Tous les membres doivent payer avant le tirage.",
            "non_payes": membres_non_a_jour
        }, status=400)


    if not membres_actifs.exists():
        return JsonResponse({"error": "Aucun membre actif"}, status=400)

    # 🔒 Vérifier versements en attente
    versements_en_attente = Versement.objects.filter(
        member__group=group,
        statut="EN_ATTENTE"
    )

    if versements_en_attente.exists():
        return JsonResponse({
            "error": "Tous les versements doivent être validés avant le tirage."
        }, status=400)

    # 🔁 Détection du cycle actuel
    dernier_tirage = group.tirages.order_by("-date_tirage").first()
    cycle_actuel = dernier_tirage.cycle_number if dernier_tirage else 1

    # 👥 Gagnants du cycle courant seulement
    gagnants_ids = group.tirages.filter(
        cycle_number=cycle_actuel
    ).values_list("gagnant_id", flat=True)

    membres_restants = membres_actifs.exclude(id__in=gagnants_ids)

    # 🔄 Reset cycle automatique
    if not membres_restants.exists():
        return JsonResponse({
            "reset": True,
            "message": "Tous les membres ont gagné. Nouveau cycle."
        })

    # 🎲 Tirage sécurisé
    gagnant = random.choice(list(membres_restants))

    # 💰 Calcul montant avec reset

    filter_q = Q(member__group=group, statut="VALIDE")

    if group.date_reset:
        filter_q &= Q(date_creation__gte=group.date_reset)

    montant_total = (
        Versement.objects
        .filter(filter_q)
        .aggregate(total=Sum("montant"))["total"] or 0
    )

    # 🧠 Lock anti double tirage (important)
    if Tirage.objects.filter(
        group=group,
        gagnant=gagnant,
        cycle_number=cycle_actuel
    ).exists():
        return JsonResponse({"error": "Tirage déjà effectué pour ce membre"}, status=400)

    # 💾 Enregistrement
    Tirage.objects.create(
        group=group,
        gagnant=gagnant,
        montant=montant_total,
        cycle_number=cycle_actuel
    )

    # 🔄 RESET AUTOMATIQUE APRÈS CHAQUE TIRAGE
    from django.utils import timezone

    group.date_reset = timezone.now()
    group.save(update_fields=["date_reset"])


    # 📲 (optionnel) WhatsApp ici
    # send_whatsapp(gagnant, group)

    # ⚡ Réponse JSON (clé pour ton animation)
    return JsonResponse({
        "success": True,
        "gagnant": gagnant.alias or getattr(gagnant.user, "username", "") or getattr(gagnant.user, "phone", ""),
        "montant": montant_total,
        "cycle": cycle_actuel
    })

from django.db.models import Sum, Q
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404

def tirage_resultat_view(request, group_id, token=None):

    group = get_object_or_404(Group, id=group_id)

    # -------------------------------------------------
    # 🔐 SÉCURITÉ ACCÈS
    # -------------------------------------------------
    is_member = False

    if request.user.is_authenticated:
        is_member = group.membres.filter(user=request.user).exists()

    # accès via lien invité sécurisé
    if not is_member:
        if not token or str(getattr(group, "access_token", "")) != str(token):
            return HttpResponseForbidden("❌ Accès refusé")

    # -------------------------------------------------
    # 📊 TIRAGES
    # -------------------------------------------------
    tirages = (
        group.tirages
        .select_related("gagnant__user")
        .order_by("-date_tirage")
    )

    dernier_tirage = tirages.first()

    gagnant = None
    montant_total = 0
    cycle_actuel = 1

    # -------------------------------------------------
    # 🔁 DÉTECTION CYCLE
    # -------------------------------------------------
    if dernier_tirage:
        gagnant = dernier_tirage.gagnant
        cycle_actuel = dernier_tirage.cycle_number or 1

    # -------------------------------------------------
    # 💰 CALCUL MONTANT
    # -------------------------------------------------
    filter_q = Q(member__group=group, statut="VALIDE")

    if group.date_reset:
        filter_q &= Q(date_creation__gte=group.date_reset)

    montant_total = (
        Versement.objects
        .filter(filter_q)
        .aggregate(total=Sum("montant"))["total"] or 0
    )

    # -------------------------------------------------
    # 👥 MEMBRES
    # -------------------------------------------------
    membres_actifs = group.membres.filter(actif=True, exit_liste=False)

    # gagnants du cycle actuel
    gagnants_ids = tirages.filter(
        cycle_number=cycle_actuel
    ).values_list("gagnant_id", flat=True)

    membres_restants = membres_actifs.exclude(id__in=gagnants_ids)

    # -------------------------------------------------
    # 🎯 ÉTAT DU CYCLE
    # -------------------------------------------------
    cycle_termine = not membres_restants.exists()
    tirage_possible = membres_restants.exists()

    # 📊 progression
    total = membres_actifs.count()
    restants = membres_restants.count()
    termines = total - restants

    progress = int((termines / total) * 100) if total > 0 else 0

    # -------------------------------------------------
    # 📦 CONTEXT
    # -------------------------------------------------
    context = {
        "group": group,
        "tirages": tirages,
        "gagnant": gagnant,
        "montant_total": montant_total,
        "tirage_possible": tirage_possible,
        "cycle_actuel": cycle_actuel,
        "cycle_termine": cycle_termine,
        "nb_restants": restants,
        "progress": progress,
    }

    return render(
        request,
        "cotisationtontine/tirage_resultat.html",
        context
    )

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Group

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Group


@login_required
def historique_cycles_view(request, group_id):
    """
    Historique basé sur les tirages (solution actuelle)
    """

    group = get_object_or_404(Group, id=group_id)

    # 🔒 Sécurité
    if request.user != group.admin and not request.user.is_superuser:
        messages.error(request, "Accès non autorisé.")
        return redirect("cotisationtontine:group_detail", group_id=group.id)

    # ✅ UTILISE tirages (PAS cycles)
    tirages_list = (
        group.tirages
        .select_related("gagnant__user")
        .order_by("-date_tirage")
    )

    # 📄 Pagination
    paginator = Paginator(tirages_list, 10)
    page_number = request.GET.get("page")
    tirages = paginator.get_page(page_number)

    context = {
        "group": group,
        "tirages": tirages,
        "total_tirages": tirages_list.count(),
    }

    return render(
        request,
        "cotisationtontine/historique_cycles.html",
        context
    )

from django.core.paginator import Paginator
from django.db.models import Count, Q

@login_required
def historique_actions_view(request):
    """
    Historique global avec filtres + stats + pagination
    """

    if not request.user.is_superuser:
        messages.error(request, "Accès réservé à l’administrateur.")
        return redirect("cotisationtontine:dashboard_tontine_simple")

    logs = ActionLog.objects.select_related("user", "group").order_by("-date")

    # 🔍 FILTRES
    action_type = request.GET.get("action_type")
    group_id = request.GET.get("group")

    if action_type:
        logs = logs.filter(action_type=action_type)

    if group_id:
        logs = logs.filter(group_id=group_id)

    # 📄 Pagination
    paginator = Paginator(logs, 20)
    page_number = request.GET.get("page")
    logs = paginator.get_page(page_number)

    # 📊 STATS
    total_logs = logs.paginator.count

    actions_par_type = (
        ActionLog.objects.values("action_type")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    context = {
        "logs": logs,
        "total_logs": total_logs,
        "actions_par_type": actions_par_type,
        "selected_action": action_type,
        "selected_group": group_id,
    }

    return render(request, "cotisationtontine/historique_actions.html", context)

# =====================================================
# MEMBRES ÉLIGIBLES POUR TIRAGE
# =====================================================

def membres_eligibles_pour_tirage(group):
    """
    Retourne les membres actifs éligibles au tirage.
    Exclut les membres ayant déjà gagné dans le cycle courant.
    """

    # Membres actifs
    membres_actifs = group.membres.filter(
        actif=True,
        exit_liste=False
    )

    if not membres_actifs.exists():
        return membres_actifs  # vide

    # Membres ayant déjà gagné
    gagnants_ids = group.tirages.values_list(
        "gagnant_id",
        flat=True
    )

    membres_restants = membres_actifs.exclude(
        id__in=gagnants_ids
    )

    # 🎯 Si tout le monde a gagné → nouveau cycle
    if not membres_restants.exists():
        return membres_actifs

    return membres_restants


from django.db import transaction
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

@login_required
@transaction.atomic
def reset_cycle_view(request, group_id):

    group = get_object_or_404(Group, id=group_id)

    # 🔒 Sécurité
    if request.user != group.admin and not request.user.is_superuser:
        messages.error(request, "Accès non autorisé.")
        return redirect("cotisationtontine:group_detail", group_id=group.id)

    membres_actifs = group.membres.filter(actif=True, exit_liste=False)

    # -------------------------------------------------
    # 🧠 0. VÉRIFIER SI CYCLE TERMINÉ
    # -------------------------------------------------

    dernier_tirage = group.tirages.order_by("-date_tirage").first()
    cycle_actuel = dernier_tirage.cycle_number if dernier_tirage else 1

    gagnants_ids = group.tirages.filter(
        cycle_number=cycle_actuel
    ).values_list("gagnant_id", flat=True)

    membres_restants = membres_actifs.exclude(id__in=gagnants_ids)

    if membres_restants.exists():
        messages.error(
            request,
            "❌ Impossible de réinitialiser : le cycle n'est pas terminé."
        )
        return redirect("cotisationtontine:group_detail", group_id=group.id)

    # -------------------------------------------------
    # 🧠 1. ENREGISTRER LE CYCLE
    # -------------------------------------------------

    from .models import Cycle, EtapeCycle

    date_debut_cycle = group.date_reset or group.date_creation
    date_fin_cycle = timezone.now()

    cycle = Cycle.objects.create(
        group=group,
        date_debut=date_debut_cycle,
        date_fin=date_fin_cycle
    )

    # -------------------------------------------------
    # 🏆 2. SAUVEGARDER LES ÉTAPES
    # -------------------------------------------------

    tirages = group.tirages.filter(cycle_number=cycle_actuel)\
                           .select_related("gagnant__user")\
                           .order_by("date_tirage")

    for index, tirage in enumerate(tirages, start=1):

        EtapeCycle.objects.create(
            cycle=cycle,
            numero_etape=index,
            date_etape=getattr(tirage, "date_tirage", timezone.now()),
            tirage=tirage
        )

    # -------------------------------------------------
    # 🧹 3. SUPPRIMER UNIQUEMENT LE CYCLE ACTUEL
    # -------------------------------------------------

    group.tirages.filter(cycle_number=cycle_actuel).delete()

    # -------------------------------------------------
    # 🔄 4. RESET DATE
    # -------------------------------------------------

    group.date_reset = timezone.now()
    group.save(update_fields=["date_reset"])

    # -------------------------------------------------
    # 📝 5. LOG
    # -------------------------------------------------

    from .models import ActionLog

    ActionLog.objects.create(
        user=request.user,
        group=group,
        action=f"Reset du cycle #{cycle_actuel}"
    )

    # -------------------------------------------------
    # ✅ MESSAGE
    # -------------------------------------------------

    messages.success(
        request,
        f"✅ Cycle #{cycle_actuel} archivé. Nouveau cycle démarré pour {group.nom}."
    )

    return redirect("cotisationtontine:group_detail", group_id=group.id)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from .models import Group, GroupMember, Versement


class GroupDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, group_id):

        group = get_object_or_404(Group, id=group_id)

        # 🔒 Vérification accès
        has_access = (
            group.admin_id == request.user.id
            or GroupMember.objects.filter(group=group, user=request.user).exists()
            or request.user.is_superuser
        )

        if not has_access:
            return Response({"error": "Accès refusé"}, status=403)

        membres = GroupMember.objects.filter(group=group).select_related("user")

        membres_data = []
        for membre in membres:
            total = (
                Versement.objects
                .filter(member=membre, statut="VALIDE")
                .aggregate(total=Sum("montant"))["total"] or 0
            )

            membres_data.append({
                "id": membre.id,
                "nom": membre.user.nom,
                "telephone": membre.user.phone,
                "total_verse": total
            })

        total_group = (
            Versement.objects
            .filter(member__group=group, statut="VALIDE")
            .aggregate(total=Sum("montant"))["total"] or 0
        )

        return Response({
            "id": group.id,
            "nom": group.nom,
            "montant_base": group.montant,
            "total_cotise": total_group,
            "membres": membres_data,
            "is_admin": request.user == group.admin
        })



class MyGroupAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        group = Group.objects.filter(admin=request.user).first()

        if not group:
            return Response({"has_group": False})

        return Response({
            "has_group": True,
            "group_id": group.id
        })
