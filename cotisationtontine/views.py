from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from cotisationtontine.models import Group, GroupMember, Versement, ActionLog


def landing_view(request):
    """
    Page d'accueil qui redirige vers le dashboard si l'utilisateur est connecté,
    ou affiche une page de présentation sinon.
    """
    # Si l'utilisateur est déjà connecté, rediriger vers le dashboard
    if request.user.is_authenticated:
        return redirect('cotisationtontine:dashboard_tontine_simple')

    # Sinon, afficher la page d'accueil publique
    return render(request, 'landing.html')

from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Group, GroupMember, Versement, ActionLog

@login_required
def dashboard_tontine_simple(request):

    groupes_admin = Group.objects.filter(admin=request.user)

    groupes_membre = Group.objects.filter(
        membres__user=request.user   # ✅ CORRECTION ICI
    ).exclude(admin=request.user).distinct()

    dernieres_actions = (
        ActionLog.objects
        .filter(user=request.user)
        .order_by('-date')[:10]
    )

    total_versements = (
        Versement.objects
        .filter(
            member__user=request.user,
            statut="VALIDE"
        )
        .aggregate(total=Sum('montant'))['total'] or 0
    )

    total_groupes = (
        Group.objects
        .filter(membres__user=request.user)   # ✅ CORRECTION ICI
        .distinct()
        .count()
    )

    date_limite = timezone.now() - timedelta(days=30)

    versements_recents = (
        Versement.objects
        .filter(
            member__user=request.user,
            date_creation__gte=date_limite
        )
        .select_related('member__user', 'member__group')
        .order_by('-date_creation')
    )[:5]

    stats_groupes_admin = []

    for groupe in groupes_admin:

        total_membres = groupe.membres.count()   # ✅ CORRECTION ICI

        total_versements_groupe = (
            Versement.objects
            .filter(
                member__group=groupe,
                statut="VALIDE"
            )
            .aggregate(total=Sum('montant'))['total'] or 0
        )

        stats_groupes_admin.append({
            'groupe': groupe,
            'membres_count': total_membres,
            'versements_total': total_versements_groupe
        })

    context = {
        "groupes_admin": groupes_admin,
        "groupes_membre": groupes_membre,
        "dernieres_actions": dernieres_actions,
        "total_versements": total_versements,
        "total_groupes": total_groupes,
        "versements_recents": versements_recents,
        "stats_groupes_admin": stats_groupes_admin,
    }

    return render(request, "cotisationtontine/dashboard.html", context)

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

@login_required
def group_list_view(request):
    """
    Affiche la liste des groupes :
    - Tous les groupes si super admin
    - Sinon, seulement ceux créés par l'utilisateur ou ceux où l'utilisateur est membre
    """
    if request.user.is_super_admin:
        groupes = Group.objects.all()
    else:
        # Groupes dont l'utilisateur est admin OU membre
        groupes = Group.objects.filter(
            Q(admin=request.user) |  # Utilisez Q directement sans le préfixe models
            Q(membres__user=request.user)
        ).distinct()

    return render(request, 'cotisationtontine/group_list.html', {
        'groupes': groupes
    })


from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db.models import Sum, Q, Value, DecimalField, OuterRef, Subquery
from django.db.models.functions import Coalesce

from .models import Group, GroupMember, Versement, ActionLog

@login_required
def group_detail(request, group_id):

    group = get_object_or_404(Group, id=group_id)

    # =====================================================
    # 🔒 Vérification accès
    # =====================================================

    has_access = (
        group.admin_id == request.user.id
        or GroupMember.objects.filter(group=group, user=request.user).exists()
        or getattr(request.user, "is_super_admin", False)
        or request.user.is_superuser
    )

    if not has_access:
        messages.error(request, "⚠️ Vous n'avez pas accès à ce groupe.")
        return redirect("cotisationtontine:group_list")

    # =====================================================
    # Relation reverse (GroupMember -> Versement)
    # =====================================================

    rel_lookup = "versements"  # doit correspondre au related_name du modèle Versement

    # =====================================================
    # Sous-requête : dernier versement
    # =====================================================

    last_qs = Versement.objects.filter(member=OuterRef("pk"))

    if group.date_reset:
        last_qs = last_qs.filter(date_creation__gte=group.date_reset)

    last_qs = last_qs.order_by("-date_creation")

    # =====================================================
    # Agrégations par membre
    # =====================================================

    sum_filter = Q()

    if group.date_reset:
        sum_filter &= Q(**{f"{rel_lookup}__date_creation__gte": group.date_reset})

    membres = (
        GroupMember.objects.filter(group=group)
        .select_related("user")
        .annotate(
            total_montant=Coalesce(
                Sum(f"{rel_lookup}__montant", filter=sum_filter),
                Value(0, output_field=DecimalField(max_digits=12, decimal_places=0)),
                output_field=DecimalField(max_digits=12, decimal_places=0),
            ),
            last_amount=Subquery(last_qs.values("montant")[:1]),
            last_date=Subquery(last_qs.values("date_creation")[:1]),
        )
        .order_by("id")
    )

    # =====================================================
    # Total global du groupe
    # =====================================================

    total_filter = Q(member__group=group)

    if group.date_reset:
        total_filter &= Q(date_creation__gte=group.date_reset)

    total_montant = (
        Versement.objects.filter(total_filter)
        .aggregate(
            total=Coalesce(
                Sum("montant"),
                Value(0, output_field=DecimalField(max_digits=12, decimal_places=0)),
                output_field=DecimalField(max_digits=12, decimal_places=0),
            )
        )["total"]
    )

    # =====================================================
    # Dernières actions
    # =====================================================

    actions = (
        ActionLog.objects
        .filter(group=group)
        .select_related("user")
        .order_by("-date")[:10]
    )

    # =====================================================
    # Lien d’invitation
    # =====================================================

    code = None
    for field in ("code_invitation", "invitation_token", "uuid"):
        if hasattr(group, field) and getattr(group, field):
            code = str(getattr(group, field))
            break

    invite_arg = code if code else str(group.id)

    invite_url = request.build_absolute_uri(
        reverse("accounts:inscription_et_rejoindre", args=[invite_arg])
    )

    user_is_admin = (
        request.user == group.admin
        or getattr(request.user, "is_super_admin", False)
        or request.user.is_superuser
    )

    if user_is_admin:
        request.session["last_invitation_link"] = invite_url

    # =====================================================
    # Context final
    # =====================================================

    context = {
        "group": group,
        "membres": membres,
        "total_montant": total_montant,
        "admin_user": group.admin,
        "actions": actions,
        "user_is_admin": user_is_admin,
        "invite_url": invite_url,
        "last_invitation_link": request.session.get("last_invitation_link"),
    }

    return render(request, "cotisationtontine/group_detail.html", context)

import json
from decimal import Decimal, ROUND_HALF_UP
import requests

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse, HttpRequest, HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

#from .models import GroupMember, Versement

from django.shortcuts import render

@login_required
def dashboard(request):
    action_logs = ActionLog.objects.filter(user=request.user).order_by('-date')[:10]
    return render(request, 'cotisationtontine/dashboard.html', {
        'action_logs': action_logs
    })

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

#from .models import GroupMember, Versement


# ==========================================
# DECLARATION VERSEMENT CAISSE
# ==========================================

@login_required
@transaction.atomic
def initier_versement(request, member_id):

    member = get_object_or_404(GroupMember.objects.select_related("group", "user"), id=member_id)
    group = member.group

    if request.method == "GET":
        return render(
            request,
            "cotisationtontine/initier_versement.html",
            {"member": member, "group": group}
        )

    montant_raw = (request.POST.get("montant") or "").replace(",", ".").strip()

    try:
        montant = Decimal(montant_raw)
    except Exception:
        messages.error(request, "Montant invalide.")
        return redirect("cotisationtontine:initier_versement", member_id=member_id)

    if montant <= 0:
        messages.error(request, "Le montant doit être supérieur à 0.")
        return redirect("cotisationtontine:initier_versement", member_id=member_id)

    montant = montant.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    Versement.objects.create(
        member=member,
        montant=montant,
        methode="CAISSE",
        statut="EN_ATTENTE"
    )

    messages.success(request, "Versement enregistré. En attente de validation par l’administrateur.")
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


# =====================================================
# TIRAGE AU SORT (SANS PAIEMENT / SANS PAYDUNYA)
# =====================================================

@login_required
@transaction.atomic
def tirage_au_sort_view(request, group_id):

    group = get_object_or_404(Group, id=group_id)

    # 🔒 Sécurité : admin ou superuser uniquement
    if request.user != group.admin and not request.user.is_superuser:
        messages.error(request, "Accès non autorisé.")
        return redirect("cotisationtontine:group_detail", group_id=group.id)

    # Membres actifs
    membres_actifs = group.membres.filter(actif=True, exit_liste=False)

    if not membres_actifs.exists():
        messages.error(request, "Aucun membre actif.")
        return redirect("cotisationtontine:group_detail", group_id=group.id)

    # =====================================================
    # 1️⃣ BLOQUER SI VERSEMENTS NON VALIDÉS
    # =====================================================
    versements_en_attente = Versement.objects.filter(
        member__group=group,
        statut="EN_ATTENTE"
    )

    if versements_en_attente.exists():
        messages.error(request, "Tous les versements doivent être validés avant le tirage.")
        return redirect("cotisationtontine:group_detail", group_id=group.id)

    # =====================================================
    # 2️⃣ MEMBRES AYANT DÉJÀ GAGNÉ (cycle courant)
    # =====================================================
    gagnants_ids = group.tirages.values_list("gagnant_id", flat=True)

    membres_restants = membres_actifs.exclude(id__in=gagnants_ids)

    # =====================================================
    # 3️⃣ SI TOUT LE MONDE A GAGNÉ → RESET
    # =====================================================
    if not membres_restants.exists():
        messages.success(
            request,
            "Tous les membres ont gagné. Le cycle va être réinitialisé."
        )
        return redirect("cotisationtontine:reset_cycle", group_id=group.id)

    # =====================================================
    # 4️⃣ TIRAGE
    # =====================================================
    gagnant = random.choice(list(membres_restants))

    # Calcul du montant
    if group.montant_fixe_gagnant is None:
        montant_total = group.montant_base * membres_actifs.count()
        group.montant_fixe_gagnant = montant_total
        group.save(update_fields=["montant_fixe_gagnant"])
    else:
        montant_total = group.montant_fixe_gagnant

    # Création du tirage
    Tirage.objects.create(
        group=group,
        gagnant=gagnant,
        montant=montant_total,
    )

    messages.success(
        request,
        f"🎉 {gagnant.user.username} a gagné {montant_total} FCFA !"
    )

    return redirect("cotisationtontine:tirage_resultat", group_id=group.id)


# =====================================================
# PAGE RÉSULTAT DU TIRAGE
# =====================================================

@login_required
def tirage_resultat_view(request, group_id):

    group = get_object_or_404(Group, id=group_id)

    tirages = group.tirages.select_related("gagnant__user").order_by("-date_tirage")
    dernier_tirage = tirages.first()

    gagnant = None
    montant_total = 0

    if dernier_tirage:
        gagnant = dernier_tirage.gagnant
        montant_total = dernier_tirage.montant

    # Vérifier s’il reste des membres à tirer
    membres_actifs = group.membres.filter(actif=True, exit_liste=False)
    gagnants_ids = tirages.values_list("gagnant_id", flat=True)
    membres_restants = membres_actifs.exclude(id__in=gagnants_ids)

    tirage_possible = membres_restants.exists()

    context = {
        "group": group,
        "tirages": tirages,
        "gagnant": gagnant,
        "montant_total": montant_total,
        "tirage_possible": tirage_possible,
    }

    return render(
        request,
        "cotisationtontine/tirage_resultat.html",
        context
    )


from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from .models import Group, Tirage


@login_required
def historique_cycles_view(request, group_id):
    """
    Affiche l'historique des tirages d'un groupe.
    """

    group = get_object_or_404(Group, id=group_id)

    tirages = (
        group.tirages
        .select_related("gagnant__user")
        .order_by("-date_tirage")
    )

    return render(
        request,
        "cotisationtontine/historique_cycles.html",
        {
            "group": group,
            "tirages": tirages,
        }
    )

# cotisationtontine/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from .models import ActionLog


# =====================================================
# HISTORIQUE DES ACTIONS
# =====================================================

@login_required
def historique_actions_view(request):
    """
    Affiche l'historique global des actions enregistrées dans ActionLog.
    """

    logs = (
        ActionLog.objects
        .select_related("user", "group")
        .order_by("-date")
    )

    return render(
        request,
        "cotisationtontine/historique_actions.html",
        {
            "logs": logs
        }
    )


# =====================================================
# MEMBRES ÉLIGIBLES POUR TIRAGE
# =====================================================

def membres_eligibles_pour_tirage(group):
    """
    Retourne les membres actifs éligibles au tirage.
    Exclut le dernier gagnant si nécessaire.
    """

    # Membres actifs du groupe
    membres = group.membres.filter(actif=True, exit_liste=False)

    # Si 1 membre ou moins → pas d'exclusion
    if membres.count() <= 1:
        return membres

    # Récupérer le dernier tirage
    dernier_tirage = group.tirages.order_by("-date_tirage").first()

    # Exclure le dernier gagnant si existant
    if dernier_tirage and dernier_tirage.gagnant:
        membres = membres.exclude(id=dernier_tirage.gagnant.id)

    return membres