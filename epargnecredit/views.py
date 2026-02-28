from .models import Group, GroupMember, Versement

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from epargnecredit.models import Group, GroupMember, Versement, ActionLog


def landing_view(request):
    """
    Page d'accueil qui redirige vers le dashboard si l'utilisateur est connecté,
    ou affiche une page de présentation sinon.
    """
    # Si l'utilisateur est déjà connecté, rediriger vers le dashboard
    if request.user.is_authenticated:
        return redirect('epargnecredit:dashboard_epargne_credit')

    # Sinon, afficher la page d'accueil publique
    return render(request, 'landing.html')


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

#from epargnecredit.models import Group, Versement, ActionLogEC  # adapter selon tes modèles
from epargnecredit.models import Group, Versement, ActionLog

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta
#from .models import Group, GroupMember, Versement, ActionLog

from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum

#from .models import Group, Versement, ActionLog  # adapte l’import si nécessaire

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from django.urls import reverse, NoReverseMatch
from datetime import timedelta

# Imports modèles (adapte si l’emplacement diffère)
from .models import Group, Versement
# ActionLog peut ne pas exister : on protège l’import
try:
    from .models import ActionLog
except Exception:
    ActionLog = None  # on gérera plus bas

from epargnecredit.decorators import validation_required

from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse, NoReverseMatch
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required

from .models import Group, ActionLog, Versement


@login_required
def dashboard_epargne_credit(request):

    try:
        attente_url = reverse("accounts:attente_validation")
    except NoReverseMatch:
        attente_url = reverse("accounts:login")

    if not request.user.is_superuser and not getattr(request.user, "is_validated", False):
        messages.error(
            request,
            "⛔ Votre compte doit être validé par l’administrateur avant d’accéder à l’application Épargne & Crédit."
        )
        return redirect(attente_url)

    # ============================
    # Groupes
    # ============================

    groupes_admin = Group.objects.filter(admin=request.user)

    groupes_membre = Group.objects.filter(
        membres_ec=request.user   # ✅ CORRECTION FINALE
    ).exclude(admin=request.user).distinct()

    # ============================
    # Actions récentes
    # ============================

    dernieres_actions = ActionLog.objects.filter(
        user=request.user
    ).order_by('-date')[:10]

    # ============================
    # Total versements validés utilisateur
    # ============================

    total_versements = (
        Versement.objects.filter(
            member__user=request.user,
            statut="VALIDE"
        ).aggregate(total=Sum('montant'))['total'] or 0
    )

    # ============================
    # Total groupes
    # ============================

    total_groupes = groupes_membre.count() + groupes_admin.count()

    # ============================
    # Versements récents (30 jours)
    # ============================

    date_limite = timezone.now() - timedelta(days=30)

    versements_recents = (
        Versement.objects.filter(
            member__user=request.user,
            date_creation__gte=date_limite
        )
        .select_related('member__user', 'member__group')
        .order_by('-date_creation')[:5]
    )

    # ============================
    # Statistiques groupes admin
    # ============================

    stats_groupes_admin = []

    for groupe in groupes_admin:

        total_membres = groupe.membres_ec.count()

        total_versements_groupe = (
            Versement.objects.filter(
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

    return render(request, "epargnecredit/dashboard.html", context)

# Optionnel : vue simple fallback
def dashboard_view(request):
    return render(request, "epargnecredit/dashboard.html")

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

from epargnecredit.forms import GroupForm, GroupMemberForm, VersementForm
from epargnecredit.models import Group, GroupMember, Invitation, Versement, ActionLog
from accounts.models import CustomUser
from accounts.utils import envoyer_invitation


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.urls import reverse
from epargnecredit.forms import GroupForm, GroupMemberForm
from epargnecredit.models import Group, GroupMember
from accounts.models import CustomUser
from epargnecredit.utils import envoyer_invitation  # ta fonction de simulation WhatsApp/SMS

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction, IntegrityError
from django.shortcuts import render, redirect
from django.urls import reverse

from .forms import GroupForm
#from .models import Group, GroupMember
from .utils import envoyer_invitation


@login_required
@transaction.atomic
def ajouter_groupe_view(request):
    """
    Création d'un nouveau groupe par un utilisateur connecté :
    1) Création du groupe (parent) avec l'utilisateur comme admin
    2) Ajout de l'admin comme membre du groupe parent
    3) Création automatique du groupe de remboursement (enfant) lié au parent
    4) Génération d'un lien d'invitation pour le groupe parent
    5) Envoi de l'invitation (simulation WhatsApp/SMS)
    """
    if request.method == "POST":
        form = GroupForm(request.POST)
        if form.is_valid():
            try:
                # 1) Groupe parent
                group = form.save(commit=False)
                group.admin = request.user
                group.is_remboursement = False
                group.parent_group = None
                group.save()

                # 2) Admin -> membre du groupe parent (évite doublon)
                GroupMember.objects.get_or_create(
                    group=group,
                    user=request.user,
                    defaults={"montant": 0}
                )

                # 3) Groupe de remboursement (enfant)
                group_remb = Group.objects.create(
                    nom=f"{group.nom} — Remboursement",
                    admin=request.user,
                    is_remboursement=True,
                    parent_group=group,
                    montant_base=0  # neutre pour la vue remboursement
                )
                # ⚠️ Si ta group_list n'affiche que les groupes où l'utilisateur est MEMBRE
                # et pas ADMIN, décommente pour ajouter l'admin aussi comme membre :
                # GroupMember.objects.get_or_create(group=group_remb, user=request.user, defaults={"montant": 0})

                # 4) Lien d'invitation (groupe parent)
                lien_invitation = request.build_absolute_uri(
                    reverse("accounts:inscription_et_rejoindre", args=[str(group.code_invitation)])
                )

                # 5) Simulation d'envoi
                envoyer_invitation(request.user.phone, lien_invitation)

                # Lien vers la page détail remboursement
                lien_remb = reverse("epargnecredit:group_detail_remboursement", args=[group_remb.id])

                messages.success(
                    request,
                    (
                        f"Groupe « {group.nom} » créé, vous avez été ajouté comme membre. "
                        f"Un groupe de remboursement a également été créé : "
                        f"<a href='{lien_remb}'>voir le groupe de remboursement</a>."
                    )
                )
                return redirect("epargnecredit:dashboard_epargne_credit")

            except IntegrityError as e:
                # Ex: contrainte 'unique_one_remboursement_per_parent_ec'
                messages.error(request, f"Conflit de création (intégrité) : {e}")
            except Exception as e:
                messages.error(request, f"Erreur lors de la création du groupe : {str(e)}")
    else:
        form = GroupForm()

    return render(
        request,
        "epargnecredit/ajouter_groupe.html",
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

    if group.admin != request.user:
        messages.error(request, "⚠️ Vous n'avez pas les droits pour ajouter un membre à ce groupe.")
        return redirect("epargnecredit:dashboard_epargne_credit")

    if request.method == "POST":
        form = GroupMemberForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data["phone"]
            nom = form.cleaned_data["nom"]

            # Crée ou récupère l'utilisateur
            user, created_user = CustomUser.objects.get_or_create(
                phone=phone,
                defaults={"nom": nom or f"Utilisateur {phone}"}
            )

            if not created_user and user.nom != nom:
                messages.warning(
                    request,
                    f"⚠️ Ce numéro est déjà associé à {user.nom}. Le nom fourni ({nom}) a été ignoré."
                )
                nom = user.nom

            # Vérifie si le membre existe déjà
            if GroupMember.objects.filter(group=group, user=user).exists():
                messages.info(request, f"ℹ️ {user.nom} est déjà membre du groupe {group.nom}.")
                return redirect("epargnecredit:group_detail", group_id=group.id)

            # Vérifie si le nom existe déjà dans le groupe avec un autre numéro
            existing_members_same_name = GroupMember.objects.filter(
                group=group,
                user__nom=nom
            ).exclude(user__phone=phone)
            alias = None
            if existing_members_same_name.exists():
                messages.warning(
                    request,
                    f"⚠️ Le nom '{nom}' existe déjà dans le groupe avec un autre numéro. "
                    f"Un alias sera créé pour éviter la confusion."
                )
                alias = f"{nom} ({phone})"

            # Ajout du membre
            group_member = GroupMember.objects.create(
                group=group,
                user=user,
                montant=0,
                alias=alias
            )

            # Message de confirmation
            messages.success(
                request,
                f"✅ {alias if alias else user.nom} a été ajouté au groupe {group.nom}."
            )

            # TODO: Simuler envoi WhatsApp ou SMS
            # message = f"Bonjour {user.nom}, vous avez été ajouté au groupe {group.nom} sur YaayESS. Connectez-vous avec votre numéro {phone}."
            # envoyer_invitation(phone, message)

            return redirect("epargnecredit:group_detail", group_id=group.id)
    else:
        form = GroupMemberForm()

    return render(
        request,
        "epargnecredit/ajouter_membre.html",
        {"group": group, "form": form}
    )

from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse

from .models import Group, GroupMember, Versement, ActionLog

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from .models import Group

@login_required
def group_list_view(request):
    """
    Affiche la liste des groupes :
    - Tous les groupes si super admin
    - Sinon, seulement ceux créés par l'utilisateur ou ceux où il est membre
    (inclut aussi les groupes de remboursement)
    """
    if getattr(request.user, "is_super_admin", False):
        groupes = Group.objects.all()
    else:
        groupes = Group.objects.filter(
            Q(admin=request.user) |
            Q(membres_ec=request.user)
        ).distinct()

    return render(request, "epargnecredit/group_list.html", {"groupes": groupes})



# epargnecredit/views.py (extrait)
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, OuterRef, Subquery, Value, DecimalField
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse

from .models import Group, GroupMember, Versement, ActionLog, PretDemande


@login_required
def group_detail(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    # =============================
    # Vérification accès
    # =============================
    has_access = (
        group.admin_id == request.user.id
        or GroupMember.objects.filter(group=group, user=request.user).exists()
        or getattr(request.user, "is_super_admin", False)
    )

    if not has_access:
        messages.error(request, "⚠️ Vous n'avez pas accès à ce groupe.")
        return redirect("epargnecredit:group_list")

    # =============================
    # Groupe remboursement
    # =============================
    remb_group = None
    if hasattr(group, "get_remboursement_group") and not group.is_remboursement:
        remb_group = group.get_remboursement_group()

    # =============================
    # Sous-requête dernier versement
    # =============================
    last_qs = Versement.objects.filter(member=OuterRef("pk"))

    if group.date_reset:
        last_qs = last_qs.filter(date_creation__gte=group.date_reset)

    last_qs = last_qs.order_by("-date_creation")

    # =============================
    # Agrégation montants membres
    # =============================
    sum_filter = Q()
    if group.date_reset:
        sum_filter &= Q(versements_ec__date_creation__gte=group.date_reset)

    membres = (
        GroupMember.objects.filter(group=group)
        .select_related("user")
        .annotate(
            total_montant=Coalesce(
                Sum("versements_ec__montant", filter=sum_filter),
                Value(0, output_field=DecimalField(max_digits=12, decimal_places=0)),
            ),
            last_amount=Subquery(last_qs.values("montant")[:1]),
            last_date=Subquery(last_qs.values("date_creation")[:1]),
        )
        .order_by("id")
    )

    # =============================
    # Total groupe
    # =============================
    total_filter = Q(member__group=group)
    if group.date_reset:
        total_filter &= Q(date_creation__gte=group.date_reset)

    total_montant = (
        Versement.objects.filter(total_filter)
        .aggregate(
            total=Coalesce(
                Sum("montant"),
                Value(0, output_field=DecimalField(max_digits=12, decimal_places=0)),
            )
        )["total"]
    )

    # =============================
    # Logs actions
    # =============================
    actions = ActionLog.objects.filter(group=group).order_by("-date")[:10]

    # =============================
    # Demandes de prêt en attente
    # =============================
    pending_prets = PretDemande.objects.filter(
        member__group=group,
        statut="PENDING"
    ).select_related("member__user").order_by("-created_at")

    # =============================
    # Lien invitation
    # =============================
    code = None
    for field in ("code_invitation", "uuid"):
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
    )

    context = {
        "group": group,
        "membres": membres,
        "total_montant": total_montant,
        "admin_user": group.admin,
        "actions": actions,
        "user_is_admin": user_is_admin,
        "invite_url": invite_url,
        "remb_group": remb_group,
        "pending_prets": pending_prets,
    }

    return render(request, "epargnecredit/group_detail.html", context)

from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.db.models import Sum
from django.utils import timezone

#from .models import Group, GroupMember, Versement, PretDemande


@login_required
def group_detail_remboursement(request, group_id):
    group = get_object_or_404(Group, pk=group_id, is_remboursement=True)
    parent = group.parent_group  # prêt approuvé est porté par le groupe parent

    membres = list(
        GroupMember.objects.select_related('user')
        .filter(group=group)
        .order_by('user__nom', 'id')
    )
    if not membres:
        return render(request, "epargnecredit/group_detail_remboursement.html", {
            "group": group,
            "membres": [],
            "title": f"Détails Remboursement — {group.nom}",
            "totals": {
                "total_verse": Decimal("0"),
                "montant_prete_plus_interet": Decimal("0"),
                "mensualite": Decimal("0"),
                "penalites": Decimal("0"),
                "reste_a_rembourser": Decimal("0"),
            }
        })

    member_ids = [m.id for m in membres]
    user_ids = [m.user_id for m in membres]

    # Total versé par membre (sur le groupe de remboursement)
    totals_map = {
        row['member']: (row['total'] or Decimal("0"))
        for row in (
            Versement.objects
            .filter(member_id__in=member_ids)
            .values('member')
            .annotate(total=Sum('montant'))
        )
    }

    # Dernière demande APPROUVÉE par user dans le groupe parent
    loans_qs = (
        PretDemande.objects
        .filter(member__group=parent, member__user_id__in=user_ids, statut="APPROVED")
        .select_related("member", "member__user")
        .order_by('member__user_id', '-decided_at', '-id')
    )
    loans_by_user = {}
    for d in loans_qs:
        uid = d.member.user_id
        if uid not in loans_by_user:
            loans_by_user[uid] = d  # garde la plus récente

    today = timezone.now().date()

    from calendar import monthrange
    def month_add(d, n):
        year = d.year + (d.month - 1 + n) // 12
        month = (d.month - 1 + n) % 12 + 1
        last_day = monthrange(year, month)[1]
        from datetime import date
        day = min(d.day, last_day)
        return date(year, month, day)

    # Calcule les montants par membre
    for m in membres:
        # Total versé (arrondi entier FCFA)
        m.total_verse = (totals_map.get(m.id, Decimal("0"))).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        d = loans_by_user.get(m.user_id)
        if not d:
            m.montant_prete_plus_interet = None
            m.mensualite = None
            m.penalites = None
            m.reste_a_rembourser = None
            continue

        principal = Decimal(d.montant or 0)
        taux = Decimal(d.interet or 0)         # %/mois
        nb_mois = max(int(d.nb_mois or 1), 1)
        start_date = (d.debut_remboursement or today)
        if hasattr(start_date, "date"):
            start_date = start_date.date()

        # Intérêt simple total + total dû + mensualité
        interet_total = (principal * (taux / Decimal("100")) * Decimal(nb_mois)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        total_du = (principal + interet_total).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        mensualite = (total_du / Decimal(nb_mois)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        # Échéances échues
        echeances_echues = 0
        last_due_date = None
        for i in range(nb_mois):
            due_date = month_add(start_date, i)  # i=0 -> 1re échéance
            if due_date <= today:
                echeances_echues += 1
                last_due_date = due_date
            else:
                break

        attendu = (mensualite * Decimal(echeances_echues)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        if attendu > total_du:
            attendu = total_du

        paye = m.total_verse
        retard = max(attendu - paye, Decimal("0"))

        # Pénalités: 10% du retard si > 10j après la dernière échéance échue
        penalites = Decimal("0")
        if retard > 0 and last_due_date and today > (last_due_date + timedelta(days=10)):
            penalites = (retard * Decimal("0.10")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        # Reste à rembourser (incluant pénalités)
        reste_brut = total_du - paye
        if reste_brut < 0:
            reste_brut = Decimal("0")
        reste_final = (reste_brut + penalites).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        m.montant_prete_plus_interet = total_du
        m.mensualite = mensualite
        m.penalites = penalites
        m.reste_a_rembourser = reste_final

    # ✅ Totaux pour le pied de tableau
    totals = {
        "total_verse": sum((m.total_verse or Decimal("0")) for m in membres),
        "montant_prete_plus_interet": sum((m.montant_prete_plus_interet or Decimal("0")) for m in membres),
        "mensualite": sum((m.mensualite or Decimal("0")) for m in membres),
        "penalites": sum((m.penalites or Decimal("0")) for m in membres),
        "reste_a_rembourser": sum((m.reste_a_rembourser or Decimal("0")) for m in membres),
    }
    # Arrondis à l’entier FCFA
    for k, v in totals.items():
        totals[k] = Decimal(v).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    return render(request, "epargnecredit/group_detail_remboursement.html", {
        "group": group,
        "membres": membres,
        "title": f"Détails Remboursement — {group.nom}",
        "totals": totals,
    })

# epargnecredit/views.py
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

from .models import GroupMember, Versement
from django.views.decorators.http import require_GET, require_POST


from decimal import Decimal, ROUND_HALF_UP
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import GroupMember, Versement


# ==========================================
# DECLARATION VERSEMENT CAISSE (EN ATTENTE)
# ==========================================
@login_required
@transaction.atomic
def initier_versement(request, member_id):

    member = get_object_or_404(
        GroupMember.objects.select_related("group", "user"),
        id=member_id
    )
    group = member.group

    # 🔒 Sécurité : seul le membre lui-même ou admin peut verser
    if request.user != member.user and request.user != group.admin and not request.user.is_superuser:
        messages.error(request, "Vous n’avez pas l’autorisation d’effectuer ce versement.")
        return redirect("epargnecredit:group_detail", group_id=group.id)

    if request.method == "GET":
        return render(request, "epargnecredit/initier_versement.html", {
            "member": member,
            "group": group
        })

    montant_raw = (request.POST.get("montant") or "").replace(",", ".").strip()

    try:
        montant = Decimal(montant_raw)
    except Exception:
        messages.error(request, "Montant invalide.")
        return redirect("epargnecredit:initier_versement", member_id=member_id)

    if montant <= 0:
        messages.error(request, "Le montant doit être supérieur à 0.")
        return redirect("epargnecredit:initier_versement", member_id=member_id)

    montant = montant.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    Versement.objects.create(
        member=member,
        montant=montant,
        methode="CAISSE",
        statut="EN_ATTENTE"
    )

    messages.success(request, "Versement enregistré. En attente de validation.")
    return redirect("epargnecredit:group_detail", group_id=group.id)


# ==========================================
# VALIDATION ADMIN
# ==========================================
from django.views.decorators.http import require_POST

from django.views.decorators.http import require_POST
from django.db.models import Sum
from .utils_pdf import generer_recu_pdf
from .utils_notification import notifier_validation_versement


@login_required
@require_POST
@transaction.atomic
def valider_versement(request, versement_id):

    versement = get_object_or_404(
        Versement.objects.select_related("member__group", "member__user"),
        id=versement_id
    )
    group = versement.member.group

    # 🔒 Permission admin uniquement
    is_group_admin = (request.user == group.admin)
    is_super_admin = bool(getattr(request.user, "is_super_admin", False))
    is_superuser = request.user.is_superuser

    if not (is_group_admin or is_super_admin or is_superuser):
        messages.error(request, "Accès refusé.")
        return redirect("epargnecredit:group_detail", group_id=group.id)

    # 🔒 Empêcher double validation
    if versement.statut != "EN_ATTENTE":
        messages.warning(request, "Ce versement a déjà été traité.")
        return redirect("epargnecredit:group_detail", group_id=group.id)

    # ✅ Validation métier centralisée
    versement.valider(request.user)

    # 📄 Génération automatique reçu PDF
    try:
        generer_recu_pdf(versement)
    except Exception as e:
        print(f"Erreur génération PDF: {e}")

    # 📲 Notification WhatsApp simulée
    try:
        notifier_validation_versement(
            versement.member.user,
            versement.montant
        )
    except Exception as e:
        print(f"Erreur notification: {e}")

    messages.success(request, "Versement validé avec succès et reçu généré.")
    return redirect("epargnecredit:group_detail", group_id=group.id)


@login_required
@require_POST
@transaction.atomic
def refuser_versement(request, versement_id):

    versement = get_object_or_404(
        Versement.objects.select_related("member__group"),
        id=versement_id
    )
    group = versement.member.group

    if request.user != group.admin and not request.user.is_superuser:
        messages.error(request, "Accès refusé.")
        return redirect("epargnecredit:group_detail", group_id=group.id)

    if versement.statut != "EN_ATTENTE":
        messages.warning(request, "Ce versement a déjà été traité.")
        return redirect("epargnecredit:group_detail", group_id=group.id)

    versement.refuser(request.user)

    messages.success(request, "Versement refusé.")
    return redirect("epargnecredit:group_detail", group_id=group.id)


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum
from .models import ActionLog
from epargnecredit.models import Group, GroupMember
#from accounts.models import Group, Member
#from cotisationtontine.models import CotisationTontine  # Si utilisé pour versements

@login_required
def dashboard(request):
    # ✅ Récupérer le groupe de l'utilisateur
    try:
        group = Group.objects.get(admin=request.user)
    except Group.DoesNotExist:
        group = None

    # ✅ Membres du groupe
    membres = Member.objects.filter(group=group) if group else []

    # ✅ Logs d'actions (limités à 10)
    action_logs = ActionLog.objects.filter(group=group).order_by('-date')[:10]

    # ✅ Total des versements validés (si CotisationTontine utilisé pour Épargne)
    total_versements = 0
    if group:
        total_versements = CotisationTontine.objects.filter(
            member__group=group,
            statut="valide"
        ).aggregate(total=Sum('montant'))['total'] or 0

    # ✅ Passer les données au template
    return render(request, 'epargnecredit/dashboard.html', {
        'group': group,
        'membres': membres,
        'action_logs': action_logs,
        'total_versements': total_versements
    })


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.apps import apps

from django.http import HttpRequest, HttpResponse
from django.urls import reverse

#from .models import Group, GroupMember, EpargneCredit, Versement


# =================================================================
# Réinitialisation du cycle (purge des versements & épargne/crédit)
# =================================================================
@login_required
@transaction.atomic
def reset_cycle_view(request: HttpRequest, group_id: int) -> HttpResponse:
    """
    Réinitialise le groupe d'épargne/crédit :
      - Permissions : admin du groupe OU superuser/super_admin.
      - GET  : affiche la page de confirmation.
      - POST : remet à zéro les soldes membres (si champ présent),
               supprime les écritures EpargneCredit et Versement,
               met à jour la date de reset du groupe.
    ⚠️ Cette action supprime les versements (irréversible).
    """
    group = get_object_or_404(Group, id=group_id)

    user = request.user
    is_group_admin = (user == getattr(group, "admin", None))
    is_superuser = getattr(user, "is_superuser", False) or getattr(user, "is_super_admin", False)
    if not (is_group_admin or is_superuser):
        messages.error(request, "Vous n'avez pas la permission de réinitialiser ce groupe.")
        return redirect("dashboard_epargne_credit")

    if request.method != "POST":
        # Page de confirmation
        members = GroupMember.objects.filter(group=group).select_related("user")
        return render(
            request,
            "epargnecredit/confirm_reset_cycle.html",
            {"group": group, "members": members, "date_reset_precedent": getattr(group, "date_reset", None)},
        )

    # --------- POST : exécuter le reset ---------
    members = GroupMember.objects.filter(group=group)

    # 1) Remettre à zéro les montants des membres (si champ 'montant' existe)
    for m in members:
        if hasattr(m, "montant"):
            m.montant = 0
            m.save(update_fields=["montant"])
        else:
            # Si pas de champ 'montant', on ignore silencieusement
            pass

    # 2) Supprimer les écritures métiers (épargne/crédit) liées au groupe
    EpargneCredit.objects.filter(member__group=group).delete()

    # 3) Supprimer les versements (tu as demandé à réinitialiser les versements)
    Versement.objects.filter(member__group=group).delete()

    # 4) Date de reset sur le groupe
    group.date_reset = timezone.now()
    group.save(update_fields=["date_reset"])

    messages.success(
        request,
        f"✅ Le cycle du groupe « {getattr(group, 'nom', group.id)} » a été réinitialisé avec succès."
    )
    return redirect("epargnecredit:group_detail", group_id=group.id)


# ==================================
# Historique des cycles (si disponible)
# ==================================
@login_required
def historique_cycles_view(request: HttpRequest, group_id: int) -> HttpResponse:
    """
    Affiche l'historique des cycles passés d'un groupe si le modèle Cycle existe.
    Tolérant : si le modèle n’existe pas, on rend une page vide.
    """
    group = get_object_or_404(Group, id=group_id)

    try:
        Cycle = apps.get_model("epargnecredit", "Cycle")
    except LookupError:
        Cycle = None

    anciens_cycles = []
    if Cycle is not None:
        anciens_cycles = (
            Cycle.objects.filter(group=group)
            .exclude(date_fin__isnull=True)  # cycles terminés
            .prefetch_related("etapes__tirage__beneficiaire__user")
            .order_by("-date_debut")
        )

    return render(
        request,
        "epargnecredit/historique_cycles.html",
        {"group": group, "anciens_cycles": anciens_cycles},
    )


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import ActionLog

@login_required
def historique_actions_view(request):
    """
    Affiche l'historique des actions enregistrées dans ActionLog.
    """
    # Récupération des logs déjà triés via Meta.ordering
    logs = ActionLog.objects.select_related("user")

    return render(request, "epargnecredit/historique_actions.html", {
        "logs": logs
    })

# epargnecredit/views.py (ajoute en haut si pas déjà)
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.db import transaction

from .models import Group, GroupMember, Versement, PretDemande  # 🔹 PretDemande
from .forms import PretDemandeForm

# ------------------------------------------------
# Créer une demande de prêt (membre ou admin)
# ------------------------------------------------
# epargnecredit/views.py
from django.db import transaction, IntegrityError
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import GroupMember, PretDemande
from .forms import PretDemandeForm

@login_required
@transaction.atomic
def demande_pret(request, member_id: int):
    member = get_object_or_404(
        GroupMember.objects.select_related("user", "group"),
        id=member_id
    )
    group = member.group

    # Permissions
    is_self = (request.user == member.user)
    is_group_admin = (request.user == getattr(group, "admin", None))
    is_super_admin = bool(getattr(request.user, "is_super_admin", False))

    if not (is_self or is_group_admin or is_super_admin):
        messages.error(request, "Vous n’avez pas les droits pour créer une demande de prêt.")
        return redirect("epargnecredit:group_detail", group_id=group.id)

    if request.method == "POST":
        form = PretDemandeForm(request.POST)

        if form.is_valid():

            # 🔒 1) Bloquer si prêt en attente
            if PretDemande.objects.filter(member=member, statut="PENDING").exists():
                messages.warning(request, "Une demande est déjà en attente.")
                return redirect("epargnecredit:group_detail", group_id=group.id)

            # 🔒 2) Bloquer si prêt déjà approuvé (actif)
            if PretDemande.objects.filter(member=member, statut="APPROVED").exists():
                messages.error(request, "Ce membre a déjà un prêt actif non soldé.")
                return redirect("epargnecredit:group_detail", group_id=group.id)

            try:
                demande = form.save(commit=False)
                demande.member = member
                demande.statut = "PENDING"
                demande.save()
            except IntegrityError:
                messages.warning(request, "Une demande de prêt est déjà en attente.")
                return redirect("epargnecredit:group_detail", group_id=group.id)

            messages.success(request, "Demande de prêt enregistrée.")
            return redirect("epargnecredit:group_detail", group_id=group.id)

        return render(request, "epargnecredit/demande_pret_form.html", {
            "form": form, "member": member, "group": group
        }, status=400)

    form = PretDemandeForm()
    return render(request, "epargnecredit/demande_pret_form.html", {
        "form": form, "member": member, "group": group
    })

# ------------------------------------------------
# Valider / Refuser une demande (ADMIN SEULEMENT)
# ------------------------------------------------
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db import transaction, IntegrityError
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages

from .models import PretDemande, Group, GroupMember

@login_required
@require_http_methods(["POST"])
@transaction.atomic
def pret_valider(request, pk: int):

    demande = get_object_or_404(
        PretDemande.objects.select_related("member__group", "member__user"),
        pk=pk
    )
    group = demande.member.group

    is_group_admin = (request.user == getattr(group, "admin", None))
    is_super_admin = bool(getattr(request.user, "is_super_admin", False))

    if not (is_group_admin or is_super_admin):
        messages.error(request, "Seul l’admin peut valider.")
        return redirect("epargnecredit:group_detail", group_id=group.id)

    if demande.statut != "PENDING":
        messages.info(request, "Cette demande a déjà été traitée.")
        return redirect("epargnecredit:group_detail", group_id=group.id)

    # 🔒 Vérification caisse disponible
    caisse_disponible = (
        Versement.objects.filter(
            member__group=group,
            statut="VALIDE"
        ).aggregate(total=Sum("montant"))["total"] or 0
    )

    if caisse_disponible < demande.montant:
        messages.error(request, "❌ Caisse insuffisante pour valider ce prêt.")
        return redirect("epargnecredit:group_detail", group_id=group.id)

    # Validation
    demande.statut = "APPROVED"
    demande.decided_by = request.user
    demande.decided_at = timezone.now()
    demande.commentaire = request.POST.get("commentaire", "")
    demande.save()

    # Création groupe remboursement si nécessaire
    remb = None
    if hasattr(group, "get_remboursement_group"):
        remb = group.get_remboursement_group()

    if remb is None:
        remb = Group.objects.create(
            nom=f"{group.nom} — Remboursement",
            admin=group.admin,
            is_remboursement=True,
            parent_group=group,
            montant_base=0
        )

    GroupMember.objects.get_or_create(
        group=remb,
        user=demande.member.user,
        defaults={"montant": 0}
    )

    messages.success(request, "Prêt approuvé et ajouté au groupe remboursement.")
    return redirect("epargnecredit:group_detail_remboursement", group_id=remb.id)

@login_required
@require_http_methods(["POST"])
@transaction.atomic
def pret_refuser(request, pk: int):

    demande = get_object_or_404(
        PretDemande.objects.select_related("member__group"),
        pk=pk
    )
    group = demande.member.group

    is_group_admin = (request.user == getattr(group, "admin", None))
    is_super_admin = bool(getattr(request.user, "is_super_admin", False))

    if not (is_group_admin or is_super_admin):
        messages.error(request, "Seul l’admin peut refuser.")
        return redirect("epargnecredit:group_detail", group_id=group.id)

    if demande.statut != "PENDING":
        messages.info(request, "Cette demande a déjà été traitée.")
        return redirect("epargnecredit:group_detail", group_id=group.id)

    demande.statut = "REJECTED"
    demande.decided_by = request.user
    demande.decided_at = timezone.now()
    demande.commentaire = request.POST.get("commentaire", "")
    demande.save()

    messages.success(request, "Demande refusée.")
    return redirect("epargnecredit:group_detail", group_id=group.id)


from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Q, Sum, OuterRef, Subquery, Value, DecimalField
from django.db.models.functions import Coalesce
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.db import transaction, IntegrityError

from .models import Group, GroupMember, Versement, ActionLog, PretDemande

@login_required
def pret_remboursement_detail(request, pk: int):
    """
    Affiche la répartition du remboursement d'un prêt APPROUVÉ
    entre les membres actifs du groupe (parts égales).
    Accessible à l’admin du groupe (ou super_admin).
    """
    demande = get_object_or_404(
        PretDemande.objects.select_related("member", "member__group", "member__user"),
        pk=pk,
    )
    group = demande.member.group

    # Permissions
    is_group_admin = (request.user == getattr(group, "admin", None))
    is_super_admin = bool(getattr(request.user, "is_super_admin", False))
    if not (is_group_admin or is_super_admin):
        messages.error(request, "Seul l’admin du groupe peut consulter cette page.")
        return redirect("epargnecredit:group_detail", group_id=group.id)

    if demande.statut != "APPROVED":
        messages.info(request, "Cette demande n'est pas approuvée.")
        return redirect("epargnecredit:group_detail", group_id=group.id)

    # Membres actifs du groupe (si le champ 'actif' existe)
    membres_qs = GroupMember.objects.filter(group=group).select_related("user")
    if "actif" in {f.name for f in GroupMember._meta.get_fields()}:
        membres_qs = membres_qs.filter(actif=True)

    nb_membres = membres_qs.count() or 1  # garde-fou

    # Totaux (entiers FCFA)
    total = demande.total_a_rembourser
    try:
        total = Decimal(total).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    except Exception:
        total = Decimal("0")

    mensualite = demande.mensualite
    try:
        mensualite = Decimal(mensualite).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    except Exception:
        mensualite = Decimal("0")

    # Part par membre (totale & mensuelle)
    part_totale = (total / nb_membres).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    part_mensuelle = (mensualite / nb_membres).quantize(Decimal("1"), rounding=ROUND_HALF_UP) if demande.nb_mois else part_totale

    # Préparer la liste pour le template
    repartition = []
    for m in membres_qs.order_by("id"):
        repartition.append({
            "member": m,
            "part_totale": part_totale,
            "part_mensuelle": part_mensuelle,
        })

    context = {
        "group": group,
        "demande": demande,
        "repartition": repartition,
        "total": total,
        "mensualite": mensualite,
        "nb_membres": nb_membres,
    }
    return render(request, "epargnecredit/pret_remboursement_detail.html", context)

# epargnecredit/views.py
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

from .models import Group, GroupMember, Versement
# Adaptez les imports ci-dessous selon votre code
# from .models import Credit, CreditRepayment, Penalite

@login_required
def share_cycle_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    # (Optionnel) Autoriser seulement l'admin du groupe
    try:
        if hasattr(group, "admin") and group.admin != request.user:
            messages.error(request, "Vous n’avez pas la permission d’effectuer le partage pour ce groupe.")
            return redirect("epargnecredit:group_detail", group_id)
    except Exception:
        pass

    # 1) Paramètres de base
    montant_base = getattr(group, "montant_base", None)
    if not montant_base or Decimal(montant_base) <= 0:
        messages.error(request, "Le montant de base (valeur d'une part) n’est pas défini pour ce groupe.")
        return redirect("epargnecredit:group_detail", group_id)

    montant_base = Decimal(montant_base)

    # 2) Total cotisations validées (du groupe)
    total_cotisations = (
        Versement.objects.filter(member__group=group, statut="VALIDE")
        .aggregate(s=Sum("montant"))
        .get("s") or Decimal("0")
    )

    # 3) Total intérêts collectés
    # ---- OPTION A : via remboursements (recommandé si vous suivez principal vs total)
    total_remboursements = Decimal("0")
    total_principal = Decimal("0")
    try:
        from .models import CreditRepayment  # adaptez si nécessaire
        # Si vous avez un champ 'montant' pour le total remboursé :
        total_remboursements = (
            CreditRepayment.objects.filter(credit__group=group, statut="VALIDE")
            .aggregate(s=Sum("montant"))  # ou 'montant_total_rembourse'
            .get("s") or Decimal("0")
        )
        # Et un champ 'montant_principal' ou similaire :
        total_principal = (
            CreditRepayment.objects.filter(credit__group=group, statut="VALIDE")
            .aggregate(s=Sum("montant_principal"))
            .get("s") or Decimal("0")
        )
    except Exception:
        # ---- OPTION B : via crédits (fallback si vous ne suivez pas principal dans les remboursements)
        try:
            from .models import Credit  # adaptez
            total_pret_plus_interet = (
                Credit.objects.filter(group=group, statut="REMBOURSE")
                .aggregate(s=Sum("montant_total"))  # si vous avez un champ 'montant_total' = principal + intérêts
                .get("s")
                or Decimal("0")
            )
            total_principal = (
                Credit.objects.filter(group=group, statut="REMBOURSE")
                .aggregate(s=Sum("montant_pret"))
                .get("s")
                or Decimal("0")
            )
            total_remboursements = total_pret_plus_interet
        except Exception:
            total_remboursements = Decimal("0")
            total_principal = Decimal("0")

    total_interets = (total_remboursements - total_principal)
    if total_interets < 0:
        total_interets = Decimal("0")  # sécurité si données partielles

    # 4) Total pénalités payées
    total_penalites = Decimal("0")
    try:
        from .models import Penalite  # adaptez
        total_penalites = (
            Penalite.objects.filter(member__group=group, statut="PAYE")
            .aggregate(s=Sum("montant"))
            .get("s") or Decimal("0")
        )
    except Exception:
        pass

    # 5) Nombre total de parts = total_cotisations / montant_base
    #    (peut être décimal si des cotisations ne tombent pas sur un multiple exact)
    total_parts = Decimal("0")
    if montant_base > 0:
        total_parts = (Decimal(total_cotisations) / montant_base)

    # 6) Montant à répartir = cotisations + intérêts + pénalités
    montant_global = Decimal(total_cotisations) + Decimal(total_interets) + Decimal(total_penalites)

    # 7) Montant par part
    montant_par_part = Decimal("0")
    if total_parts > 0:
        montant_par_part = (montant_global / total_parts)

    # 8) Parts par membre = (cotisations_membre / montant_base)
    #    Montant dû par membre = parts_membre * montant_par_part
    lignes = []
    membres = GroupMember.objects.filter(group=group).select_related("user")
    for m in membres:
        cotisations_membre = (
            Versement.objects.filter(member=m, statut="VALIDE")
            .aggregate(s=Sum("montant"))
            .get("s") or Decimal("0")
        )
        parts_membre = Decimal("0")
        if montant_base > 0:
            parts_membre = (Decimal(cotisations_membre) / montant_base)

        du_membre = parts_membre * montant_par_part

        lignes.append({
            "member": m,
            "nom": getattr(getattr(m, "user", None), "nom", None) or getattr(m, "user_nom", str(m)),
            "cotise": cotisations_membre,
            "parts": parts_membre,
            "du": du_membre.quantize(Decimal("0.01")),
        })

    # Tri (optionnel) : du montant dû décroissant
    lignes.sort(key=lambda x: x["du"], reverse=True)

    # Vous pouvez stocker un historique ici si besoin (modèles RepartitionHistorique/RepartitionLigne)

    # On affiche le résultat dans la page détail du groupe
    context = {
        "group": group,
        "montant_base": montant_base,
        "total_cotisations": total_cotisations,
        "total_interets": total_interets,
        "total_penalites": total_penalites,
        "montant_global": montant_global,
        "total_parts": total_parts,
        "montant_par_part": montant_par_part,
        "repartition_lignes": lignes,
    }
    messages.success(request, "La répartition de fin de cycle a été calculée.")
    return render(request, "epargnecredit/group_detail.html", context)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsOptionTwo
from rest_framework.permissions import BasePermission

class DashboardEpargneView(APIView):
    permission_classes = [IsAuthenticated, IsOptionTwo]

    def get(self, request):
        return Response({"message": "Bienvenue Épargne & Crédit"})

from accounts.permissions import IsSuperAdmin


class AdminOnlyView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]


class IsAdminOrSuper(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or request.user.is_super_admin
        )

