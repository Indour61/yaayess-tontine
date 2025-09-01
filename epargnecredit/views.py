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
from .models import Group, GroupMember, Versement, ActionLog

from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum

from .models import Group, Versement, ActionLog  # adapte l’import si nécessaire

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

@login_required
def dashboard_epargne_credit(request):
    """
    Dashboard principal avec aperçu des groupes, activités récentes et statistiques.
    Accès réservé aux comptes validés par un superuser.
    """

    # ✅ Fallback URL si l'URL d'attente n'existe pas encore
    try:
        attente_url = reverse("accounts:attente_validation")
    except NoReverseMatch:
        attente_url = reverse("accounts:login")

    # ✅ Blocage si le compte n'est pas encore validé (superuser passe)
    if not request.user.is_superuser and not getattr(request.user, "is_validated", False):
        messages.error(
            request,
            "⛔ Votre compte doit être validé par l’administrateur avant d’accéder à l’application Épargne & Crédit."
        )
        return redirect(attente_url)

    # Groupes dont l'utilisateur est administrateur
    groupes_admin = Group.objects.filter(admin=request.user)

    # Groupes dont l'utilisateur est membre (via relation membres_ec)
    groupes_membre = Group.objects.filter(
        membres_ec=request.user
    ).exclude(admin=request.user).distinct()

    # Dernières actions de l'utilisateur (si ActionLog existe)
    if ActionLog is not None:
        dernieres_actions = ActionLog.objects.filter(user=request.user).order_by('-date')[:10]
    else:
        dernieres_actions = []

    # Total des versements de l'utilisateur
    total_versements = Versement.objects.filter(
        member__user=request.user
    ).aggregate(total=Sum('montant'))['total'] or 0

    # Nombre total de groupes
    total_groupes = groupes_membre.count() + groupes_admin.count()

    # Versements récents (30 jours)
    date_limite = timezone.now() - timedelta(days=30)
    versements_recents = Versement.objects.filter(
        member__user=request.user,
        date__gte=date_limite
    ).select_related('member__user', 'member__group').order_by('-date')[:5]

    # Statistiques des groupes administrés
    stats_groupes_admin = []
    for groupe in groupes_admin:
        total_membres = getattr(groupe, "membres_ec", []).count() if hasattr(groupe, "membres_ec") else 0
        total_versements_groupe = Versement.objects.filter(
            member__group=groupe
        ).aggregate(total=Sum('montant'))['total'] or 0
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
from django.db import transaction
from django.shortcuts import render, redirect
from django.urls import reverse

from .forms import GroupForm
from .models import Group, GroupMember
from .utils import envoyer_invitation  # ta fonction de simulation WhatsApp/SMS

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

                # ✅ Crée un lien d'invitation sécurisé
                lien_invitation = request.build_absolute_uri(
                    reverse("accounts:inscription_et_rejoindre", args=[str(group.code_invitation)])
                )

                # ✅ Simule l'envoi de l'invitation
                envoyer_invitation(request.user.phone, lien_invitation)

                messages.success(
                    request,
                    f"Groupe « {group.nom} » créé avec succès et vous avez été ajouté comme membre."
                )
                return redirect("epargnecredit:dashboard_epargne_credit")

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

from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import Group, GroupMember, Versement, ActionLog


from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse

from .models import Group, GroupMember, Versement, ActionLog

@login_required
def group_list_view(request):
    """
    Affiche la liste des groupes :
    - Tous les groupes si super admin
    - Sinon, seulement ceux créés par l'utilisateur ou ceux où il est membre
    """
    if getattr(request.user, "is_super_admin", False):
        groupes = Group.objects.all()
    else:
        # Utilisation du nouveau related_name 'members'
        groupes = Group.objects.filter(
            Q(admin=request.user) |
            Q(members__user=request.user)
        ).distinct()

    return render(request, 'epargnecredit/group_list.html', {'groupes': groupes})



# epargnecredit/views.py (extrait)
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Subquery, OuterRef
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse

from .models import Group, GroupMember, Versement, ActionLog  # adapte si noms différents

# epargnecredit/views.py (extrait)

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Value, DecimalField, Subquery, OuterRef
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse

from .models import Group, GroupMember, Versement, ActionLog
from .models import Group, GroupMember, Versement, ActionLog, PretDemande  # + PretDemande

@login_required
def group_detail(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    has_access = (
        group.admin_id == getattr(request.user, "id", None)
        or GroupMember.objects.filter(group=group, user=request.user).exists()
        or getattr(request.user, "is_super_admin", False)
    )
    if not has_access:
        messages.error(request, "⚠️ Vous n'avez pas accès à ce groupe.")
        return redirect("epargnecredit:group_list")

    # --- Nom de la relation reverse GroupMember -> Versement ---
    rel_lookup = "versements_ec"

    # --- Sous-requête : dernier versement (date + montant) depuis date_reset si définie ---
    last_qs = Versement.objects.filter(member=OuterRef("pk"))
    if getattr(group, "date_reset", None):
        last_qs = last_qs.filter(date__gte=group.date_reset)
    last_qs = last_qs.order_by("-date")

    # --- Agrégations par membre ---
    sum_filter = Q()
    if getattr(group, "date_reset", None):
        sum_filter &= Q(**{f"{rel_lookup}__date__gte": group.date_reset})

    membres = (
        GroupMember.objects.filter(group=group)
        .select_related("user", "group")
        .annotate(
            total_montant=Coalesce(
                Sum(f"{rel_lookup}__montant", filter=sum_filter),
                Value(0, output_field=DecimalField(max_digits=12, decimal_places=2)),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
            last_amount=Subquery(last_qs.values("montant")[:1]),
            last_date=Subquery(last_qs.values("date")[:1]),
        )
        .order_by("id")
    )

    # --- Total groupe (filtré par reset si présent) ---
    total_filter = Q(member__group=group)
    if getattr(group, "date_reset", None):
        total_filter &= Q(date__gte=group.date_reset)

    total_montant = (
        Versement.objects.filter(total_filter)
        .aggregate(
            total=Coalesce(
                Sum("montant"),
                Value(0, output_field=DecimalField(max_digits=12, decimal_places=2)),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )["total"]
    )

    # --- Actions ---
    try:
        actions = ActionLog.objects.filter(group=group).order_by("-date")[:10]
    except Exception:
        actions = []

    # --- Lien d'invitation robuste ---
    code = None
    for field in ("code_invitation", "invitation_code", "uuid", "code"):
        if hasattr(group, field) and getattr(group, field):
            code = str(getattr(group, field))
            break
    invite_arg = code if code else str(group.id)
    invite_url = request.build_absolute_uri(
        reverse("accounts:inscription_et_rejoindre", args=[invite_arg])
    )

    user_is_admin = (request.user == group.admin) or getattr(request.user, "is_super_admin", False)
    if user_is_admin:
        request.session["last_invitation_link"] = invite_url

    # --- 🔹 Demandes de prêt en attente (admin seulement) ---
    pending_prets = PretDemande.objects.none()
    if user_is_admin:
        pending_prets = (
            PretDemande.objects
            .filter(member__group=group, statut="PENDING")
            .select_related("member", "member__user")
            .order_by("-created_at")
        )

    context = {
        "group": group,
        "membres": membres,                # total_montant / last_date / last_amount
        "total_montant": total_montant,
        "admin_user": group.admin,
        "actions": actions,
        "user_is_admin": user_is_admin,
        "invite_url": invite_url,
        "last_invitation_link": request.session.get("last_invitation_link"),
        "pending_prets": pending_prets,    # 🔹 ajouté
    }
    return render(request, "epargnecredit/group_detail.html", context)


# epargnecredit/views.py

import json
from decimal import Decimal, ROUND_HALF_UP
import requests

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

# ⬇️ Adapte ces imports selon tes modèles réels côté epargnecredit
from .models import GroupMember, Versement  # ex: from .models import Member as GroupMember, Epargne as Versement


# ===============================
# Helpers PayDunya
# ===============================
def _pd_conf():
    """
    Récupère la configuration PayDunya depuis settings.
    Compatible avec PAYDUNYA_KEYS ou PAYDUNYA (préféré).
    """
    cfg = getattr(settings, "PAYDUNYA", None) or getattr(settings, "PAYDUNYA_KEYS", None)
    if not cfg:
        raise RuntimeError("Configuration PayDunya absente (PAYDUNYA ou PAYDUNYA_KEYS).")
    for k in ("master_key", "private_key", "public_key", "token"):
        if k not in cfg or not cfg[k]:
            raise RuntimeError(f"Clé PayDunya manquante: {k}")
    return cfg


def _pd_headers(cfg):
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "PAYDUNYA-MASTER-KEY": cfg["master_key"],
        "PAYDUNYA-PRIVATE-KEY": cfg["private_key"],
        "PAYDUNYA-PUBLIC-KEY": cfg["public_key"],
        "PAYDUNYA-TOKEN": cfg["token"],
    }


def _pd_base_url(cfg):
    # PAYDUNYA["sandbox"] recommandé ; sinon bascule sur DEBUG à défaut.
    sandbox = cfg.get("sandbox", getattr(settings, "DEBUG", True)) if hasattr(cfg, "get") else getattr(settings, "DEBUG", True)
    return "https://app.paydunya.com/sandbox-api/v1" if sandbox else "https://app.paydunya.com/api/v1"


def _as_fcfa_int(amount: Decimal) -> int:
    """PayDunya attend des entiers (FCFA)."""
    return int(amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


# ===============================
# Vue: Initier un versement
# ===============================
@login_required
@transaction.atomic
def initier_versement(request: HttpRequest, member_id: int) -> HttpResponse:
    """
    - CAISSE : crée directement le Versement (pas de champ 'statut').
    - PAYDUNYA : crée la facture, redirige l’utilisateur, et attend le callback pour créer le Versement.
    """
    member = get_object_or_404(GroupMember, id=member_id)
    group = member.group
    group_id = group.id

    # --- Permissions ---
    is_self = (request.user == member.user)
    is_group_admin = (request.user == getattr(group, "admin", None))
    is_super_admin = bool(getattr(request.user, "is_super_admin", False))
    if not (is_self or is_group_admin or is_super_admin):
        messages.error(request, "Vous n'avez pas les droits pour effectuer un versement pour ce membre.")
        return redirect("epargnecredit:group_detail", group_id=group_id)

    if request.method == "GET":
        return render(request, "epargnecredit/initier_versement.html", {"member": member, "group": group})

    # --- POST ---
    montant_raw = (request.POST.get("montant") or "").replace(",", ".").strip()
    methode = (request.POST.get("methode") or "paydunya").lower()

    # Valider le montant
    try:
        montant = Decimal(montant_raw)
    except Exception:
        messages.error(request, "Montant invalide.")
        return redirect("epargnecredit:initier_versement", member_id=member_id)

    if montant <= 0:
        messages.error(request, "Le montant doit être supérieur à 0.")
        return redirect("epargnecredit:initier_versement", member_id=member_id)

    # Forcer l'entier en FCFA
    montant = montant.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    # 1) CAISSE -> on écrit immédiatement
    if methode == "caisse":
        Versement.objects.create(
            member=member,
            montant=montant,
            frais=Decimal("0"),
            methode="CAISSE",
            transaction_id=f"EC-CAISSE-{member.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
        )
        messages.success(request, f"Versement de {_as_fcfa_int(montant)} FCFA enregistré via Caisse.")
        return redirect("epargnecredit:group_detail", group_id=group_id)

    # 2) PAYDUNYA
    try:
        cfg = _pd_conf()
        headers = _pd_headers(cfg)
        base_url = _pd_base_url(cfg)
    except RuntimeError as e:
        messages.error(request, str(e))
        return redirect("epargnecredit:initier_versement", member_id=member_id)

    # Frais (exemple) : 2% + 50 FCFA
    frais_total = (montant * Decimal("0.02") + Decimal("50")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    montant_total = (montant + frais_total).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    # URLs
    callback_url = request.build_absolute_uri(reverse("epargnecredit:versement_callback"))
    return_url = request.build_absolute_uri(reverse("epargnecredit:versement_merci"))
    cancel_url = request.build_absolute_uri(reverse("epargnecredit:group_detail", args=[group_id]))

    payload = {
        "invoice": {
            "items": [
                {
                    "name": "Versement épargne",
                    "quantity": 1,
                    "unit_price": _as_fcfa_int(montant_total),
                    "total_price": _as_fcfa_int(montant_total),
                    "description": (
                        f"Versement membre {member.user.nom or member.user.phone} "
                        f"(frais: {_as_fcfa_int(frais_total)} FCFA)"
                    ),
                }
            ],
            "description": f"Paiement épargne (+{_as_fcfa_int(frais_total)} FCFA de frais)",
            "total_amount": _as_fcfa_int(montant_total),
            "currency": "XOF",
        },
        "store": {
            "name": cfg.get("store_name", "YaayESS"),
            "tagline": cfg.get("store_tagline", "Plateforme de gestion financière"),
            "website_url": cfg.get("website_url", "https://yaayess.com"),
        },
        "actions": {  # ✅ URLs à cet endroit
            "callback_url": callback_url,
            "return_url": return_url,
            "cancel_url": cancel_url,
        },
        # Ces données reviennent au callback (confirm) pour créer le Versement
        "custom_data": {
            "member_id": member.id,
            "user_id": request.user.id,
            "montant": _as_fcfa_int(montant),   # hors frais
            "frais": _as_fcfa_int(frais_total),
        },
    }

    # Création de la facture
    try:
        resp = requests.post(f"{base_url}/checkout-invoice/create", headers=headers, json=payload, timeout=20)
    except requests.exceptions.RequestException as e:
        messages.error(request, f"Erreur réseau PayDunya : {e}")
        return redirect("epargnecredit:initier_versement", member_id=member_id)

    if resp.status_code != 200:
        messages.error(request, f"Erreur PayDunya (HTTP {resp.status_code})")
        if getattr(settings, "DEBUG", False):
            try:
                messages.info(request, f"DEBUG PayDunya: {resp.text[:600]}")
            except Exception:
                pass
        return redirect("epargnecredit:initier_versement", member_id=member_id)

    try:
        data = resp.json()
    except json.JSONDecodeError:
        messages.error(request, "Réponse PayDunya invalide (JSON).")
        if getattr(settings, "DEBUG", False):
            messages.info(request, f"DEBUG PayDunya: {resp.text[:600]}")
        return redirect("epargnecredit:initier_versement", member_id=member_id)

    if getattr(settings, "DEBUG", False):
        try:
            messages.info(request, f"DEBUG PayDunya: {json.dumps(data)[:600]}")
        except Exception:
            pass

    # response_code "00" => facture créée
    if isinstance(data, dict) and data.get("response_code") == "00":
        invoice_url = None

        rt = data.get("response_text")
        # Cas 1: l'URL est directement une chaîne
        if isinstance(rt, str) and rt.startswith("http"):
            invoice_url = rt
        # Cas 2: certaines versions renvoient un dict avec invoice_url
        elif isinstance(rt, dict):
            invoice_url = rt.get("invoice_url")

        # Fallbacks possibles
        if not invoice_url:
            invoice_url = (
                data.get("invoice_url")
                or data.get("checkout_url")
                or data.get("url")
                or (data.get("data", {}).get("invoice_url") if isinstance(data.get("data"), dict) else None)
            )

        if invoice_url:
            return redirect(invoice_url)

        # Pas d'URL : si token présent, on laisse le callback finaliser
        token = data.get("token") or (rt.get("token") if isinstance(rt, dict) else None)
        if token:
            messages.warning(
                request,
                "Facture créée. Redirection indisponible ; le paiement doit être finalisé côté PayDunya."
            )
            return redirect("epargnecredit:group_detail", group_id=group_id)

        messages.warning(request, "Facture créée mais URL manquante. Retour au groupe.")
        return redirect("epargnecredit:group_detail", group_id=group_id)

    messages.error(request, f"Échec de création de facture: {data.get('response_text', 'Erreur inconnue')}")
    return redirect("epargnecredit:initier_versement", member_id=member_id)


# ===============================
# Callback PayDunya (idempotent)
# ===============================
@csrf_exempt
@transaction.atomic
def versement_callback(request: HttpRequest) -> JsonResponse:
    """
    1) Récupère le token envoyé par PayDunya
    2) Confirme côté PayDunya (endpoint confirm)
    3) Si payé, crée un Versement (idempotent via transaction_id)
    """
    try:
        payload = json.loads(request.body or "{}")
    except Exception:
        return JsonResponse({"error": "Payload invalide"}, status=400)

    token = payload.get("token") or payload.get("payout_token") or payload.get("invoice", {}).get("token")
    if not token:
        return JsonResponse({"error": "Token manquant"}, status=400)

    # Idempotence
    if Versement.objects.filter(transaction_id=token).exists():
        return JsonResponse({"message": "Déjà confirmé."}, status=200)

    try:
        cfg = _pd_conf()
        headers = _pd_headers(cfg)
        base_url = _pd_base_url(cfg)
    except RuntimeError as e:
        return JsonResponse({"error": str(e)}, status=500)

    try:
        confirm = requests.get(f"{base_url}/checkout-invoice/confirm/{token}", headers=headers, timeout=20)
    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": f"Erreur réseau PayDunya: {e}"}, status=502)

    if confirm.status_code != 200:
        return JsonResponse({"error": f"Confirm HTTP {confirm.status_code}"}, status=502)

    try:
        conf = confirm.json()
    except json.JSONDecodeError:
        return JsonResponse({"error": "Confirm JSON invalide"}, status=502)

    status_flag = str(conf.get("status", "")).lower()
    ok = (conf.get("response_code") == "00") and (status_flag in {"completed", "paid", "accepted"})
    if not ok:
        return JsonResponse({"error": f"Paiement non confirmé: {status_flag} | {conf.get('response_text')}"}, status=400)

    # Récup data pour créer l'écriture
    custom = conf.get("custom_data") if isinstance(conf.get("custom_data"), dict) else payload.get("custom_data", {})
    try:
        member_id = int(custom.get("member_id"))
        montant = Decimal(str(custom.get("montant", "0"))).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        frais = Decimal(str(custom.get("frais", "0"))).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    except Exception:
        return JsonResponse({"error": "custom_data invalide"}, status=400)

    member = GroupMember.objects.filter(id=member_id).select_related("group", "user").first()
    if not member:
        return JsonResponse({"error": "Membre introuvable"}, status=404)

    # Création idempotente
    versement, created = Versement.objects.get_or_create(
        transaction_id=token,
        defaults={
            "member": member,
            "montant": montant,
            "frais": frais,
            "methode": "PAYDUNYA",
        },
    )
    return JsonResponse({"message": "✅ Versement confirmé", "created": created}, status=200)


# ===============================
# Page Merci (retour client)
# ===============================
def versement_merci(request: HttpRequest) -> HttpResponse:
    return render(request, "epargnecredit/versement_merci.html")




from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum
from .models import ActionLog
from epargnecredit.models import Group, GroupMember
#from accounts.models import Group, Member
from cotisationtontine.models import CotisationTontine  # Si utilisé pour versements

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

from .models import Group, GroupMember, EpargneCredit, Versement


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

    # Permissions: le membre lui-même, l'admin du groupe, ou super_admin
    is_self = (request.user == member.user)
    is_group_admin = (request.user == getattr(group, "admin", None))
    is_super_admin = bool(getattr(request.user, "is_super_admin", False))
    if not (is_self or is_group_admin or is_super_admin):
        messages.error(request, "Vous n’avez pas les droits pour créer une demande de prêt pour ce membre.")
        return redirect("epargnecredit:group_detail", group_id=group.id)

    if request.method == "POST":
        form = PretDemandeForm(request.POST)
        if form.is_valid():
            try:
                # Empêcher plusieurs demandes “en attente” (contrainte DB + garde applicative)
                if PretDemande.objects.filter(member=member, statut="PENDING").exists():
                    messages.warning(request, "Une demande de prêt est déjà en attente pour ce membre.")
                    return redirect("epargnecredit:group_detail", group_id=group.id)

                demande: PretDemande = form.save(commit=False)
                demande.member = member
                demande.statut = "PENDING"
                demande.save()
            except IntegrityError as e:
                # Cas de collision avec l'unique constraint conditionnelle
                if "uniq_pending_pret_par_membre_ec" in str(e):
                    messages.warning(request, "Une demande de prêt est déjà en attente pour ce membre.")
                    return redirect("epargnecredit:group_detail", group_id=group.id)
                messages.error(request, f"Erreur base de données: {e}")
                return render(request, "epargnecredit/demande_pret_form.html", {
                    "form": form, "member": member, "group": group
                }, status=400)
            except Exception as e:
                messages.error(request, f"Erreur inattendue: {e}")
                return render(request, "epargnecredit/demande_pret_form.html", {
                    "form": form, "member": member, "group": group
                }, status=400)

            messages.success(request, "Votre demande de prêt a été enregistrée et est en attente de validation.")
            return redirect("epargnecredit:group_detail", group_id=group.id)
        else:
            # Réafficher le formulaire avec les erreurs
            return render(request, "epargnecredit/demande_pret_form.html", {
                "form": form, "member": member, "group": group
            }, status=400)
    else:
        # GET
        form = PretDemandeForm()
        return render(request, "epargnecredit/demande_pret_form.html", {
            "form": form, "member": member, "group": group
        })

# ------------------------------------------------
# Valider / Refuser une demande (ADMIN SEULEMENT)
# ------------------------------------------------
@login_required
@require_http_methods(["POST"])
@transaction.atomic
def pret_valider(request, pk: int):
    demande = get_object_or_404(PretDemande.objects.select_related("member", "member__group"), pk=pk)
    group = demande.member.group

    is_group_admin = (request.user == getattr(group, "admin", None))
    is_super_admin = bool(getattr(request.user, "is_super_admin", False))
    if not (is_group_admin or is_super_admin):
        messages.error(request, "Seul l’admin du groupe peut valider un prêt.")
        return redirect("epargnecredit:group_detail", group_id=group.id)

    if demande.statut != "PENDING":
        messages.info(request, "Cette demande a déjà été traitée.")
        return redirect("epargnecredit:group_detail", group_id=group.id)

    demande.statut = "APPROVED"
    demande.decided_by = request.user
    demande.decided_at = timezone.now()
    demande.commentaire = request.POST.get("commentaire", "")
    demande.save(update_fields=["statut", "decided_by", "decided_at", "commentaire"])

    messages.success(request, "Demande de prêt approuvée ✅")
    # 🔁 Redirige vers la page de remboursement
    return redirect("epargnecredit:pret_remboursement_detail", pk=demande.id)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def pret_refuser(request, pk: int):
    demande = get_object_or_404(PretDemande.objects.select_related("member", "member__group"), pk=pk)
    group = demande.member.group

    is_group_admin = (request.user == getattr(group, "admin", None))
    is_super_admin = bool(getattr(request.user, "is_super_admin", False))
    if not (is_group_admin or is_super_admin):
        messages.error(request, "Seul l’admin du groupe peut refuser un prêt.")
        return redirect("epargnecredit:group_detail", group_id=group.id)

    if demande.statut != "PENDING":
        messages.info(request, "Cette demande a déjà été traitée.")
        return redirect("epargnecredit:group_detail", group_id=group.id)

    demande.statut = "REJECTED"
    demande.decided_by = request.user
    demande.decided_at = timezone.now()
    demande.commentaire = request.POST.get("commentaire", "")
    demande.save(update_fields=["statut", "decided_by", "decided_at", "commentaire"])

    messages.success(request, "Demande de prêt refusée ❌")
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
