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


@login_required
def dashboard_tontine_simple(request):
    """
    Dashboard principal avec aperçu des groupes, activités récentes et statistiques.
    """
    # Groupes dont l'utilisateur est administrateur
    groupes_admin = Group.objects.filter(admin=request.user)

    # Groupes dont l'utilisateur est membre (mais pas admin)
    groupes_membre = Group.objects.filter(
        membres__user=request.user
    ).exclude(admin=request.user).distinct()

    # Dernières actions de l'utilisateur
    dernieres_actions = ActionLog.objects.filter(user=request.user).order_by('-date')[:10]

    # Total des versements de l'utilisateur - CORRECTION ICI
    # On passe par GroupMember pour accéder aux versements
    total_versements = Versement.objects.filter(
        member__user=request.user
    ).aggregate(total=Sum('montant'))['total'] or 0

    # Nombre total de groupes où l'utilisateur est membre
    total_groupes = Group.objects.filter(
        membres__user=request.user
    ).distinct().count()

    # Récupérer les versements récents (30 derniers jours)
    date_limite = timezone.now() - timedelta(days=30)
    versements_recents = Versement.objects.filter(
        member__user=request.user,
        date__gte=date_limite  # Utilisez le nom correct du champ date
    ).select_related('member__user', 'member__group').order_by('-date')[:5]

    # Statistiques des groupes administrés
    stats_groupes_admin = []
    for groupe in groupes_admin:
        total_membres = groupe.membres.count()
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
from django.db.models import Sum, OuterRef, Subquery, Q, Value, DecimalField
from django.db.models.functions import Coalesce
from django.urls import reverse

from .models import Group, GroupMember, Versement, ActionLog


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
        return redirect("cotisationtontine:group_list")

    # --- Nom de la relation reverse GroupMember -> Versement ---
    # D'après ton log, c'est bien "versements"
    rel_lookup = "versements"

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

    context = {
        "group": group,
        "membres": membres,                # total_montant / last_date / last_amount
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

from .models import GroupMember, Versement

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

from .models import GroupMember, Versement


# ===============================
# Helpers PayDunya (cohérents avec settings/.env)
# ===============================
def _paydunya_conf() -> dict:
    """
    Retourne une config normalisée à partir de settings.PAYDUNYA (dict) + fallback .env.
    Clés obligatoires: master_key, private_key, token.
    public_key est OPTIONNELLE pour l'API checkout.
    """
    s_cfg = getattr(settings, "PAYDUNYA", {}) or {}

    # Fallback .env
    env_flag = (s_cfg.get("env") or s_cfg.get("mode") or os.getenv("PAYDUNYA_ENV", "sandbox")).strip().lower()
    if env_flag in ("production", "live"):
        env_flag = "prod"
    elif env_flag not in ("prod", "sandbox"):
        env_flag = "sandbox"

    cfg = {
        "env": env_flag,  # "sandbox" | "prod"
        "master_key": (s_cfg.get("master_key") or os.getenv("PAYDUNYA_MASTER_KEY", "")).strip(),
        "private_key": (s_cfg.get("private_key") or os.getenv("PAYDUNYA_PRIVATE_KEY", "")).strip(),
        "token": (s_cfg.get("token") or os.getenv("PAYDUNYA_TOKEN", "")).strip(),
        # optionnel (non requis par l'appel HTTP)
        "public_key": (s_cfg.get("public_key") or os.getenv("PAYDUNYA_PUBLIC_KEY", "")).strip(),
        # infos boutique (facultatives)
        "store_name": s_cfg.get("store_name", getattr(settings, "PAYDUNYA_STORE_NAME", "YaayESS")),
        "store_tagline": s_cfg.get("store_tagline", getattr(settings, "PAYDUNYA_STORE_TAGLINE", "Plateforme de gestion financière")),
        "website_url": s_cfg.get("website_url", getattr(settings, "PAYDUNYA_WEBSITE_URL", "https://yaayess.com")),
    }

    # Validations hard (obligatoires)
    for k in ("master_key", "private_key", "token"):
        if not cfg[k]:
            raise RuntimeError(f"Clé PAYDUNYA manquante: {k}")

    return cfg


def _paydunya_headers(cfg: dict) -> dict:
    """
    Headers requis pour créer un checkout.
    (Pas besoin d'envoyer le PUBLIC-KEY ici.)
    """
    return {
        "Content-Type": "application/json",
        "PAYDUNYA-MASTER-KEY": cfg["master_key"],
        "PAYDUNYA-PRIVATE-KEY": cfg["private_key"],
        "PAYDUNYA-TOKEN": cfg["token"],
    }


def _paydunya_base_url(cfg: dict) -> str:
    """
    Base URL selon l'environnement.
    """
    return (
        "https://app.paydunya.com/api/v1"
        if cfg.get("env") == "prod"
        else "https://app.paydunya.com/sandbox-api/v1"
    )


def _as_fcfa_int(amount: Decimal | int | str) -> int:
    """PayDunya attend des entiers (XOF)."""
    if isinstance(amount, Decimal):
        d = amount
    else:
        d = Decimal(str(amount))
    return int(d.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


# ===============================
# Vue: Initier un versement (PAYDUNYA only)
# ===============================
@login_required
@transaction.atomic
def initier_versement(request: HttpRequest, member_id: int) -> HttpResponse:
    """
    PAYDUNYA : crée la facture, redirige l’utilisateur, et attend le callback pour créer le Versement.
    (La méthode 'caisse' a été supprimée.)
    """
    # 1) Récupération membre/groupe (pour avoir group_id dans tout redirect)
    member = get_object_or_404(GroupMember, id=member_id)
    group = member.group
    group_id = group.id

    # 2) Permissions
    is_self = (request.user == member.user)
    is_group_admin = (request.user == getattr(group, "admin", None))
    is_super_admin = bool(getattr(request.user, "is_super_admin", False))
    if not (is_self or is_group_admin or is_super_admin):
        messages.error(request, "Vous n'avez pas les droits pour effectuer un versement pour ce membre.")
        return redirect("cotisationtontine:group_detail", group_id=group_id)

    # 3) GET => affichage du formulaire
    if request.method == "GET":
        return render(request, "cotisationtontine/initier_versement.html", {"member": member, "group": group})

    # 4) POST => validation du montant
    montant_raw = (request.POST.get("montant") or "").replace(",", ".").strip()
    methode = "paydunya"

    try:
        montant = Decimal(montant_raw)
    except Exception:
        messages.error(request, "Montant invalide.")
        return redirect("cotisationtontine:initier_versement", member_id=member_id)

    if montant <= 0:
        messages.error(request, "Le montant doit être supérieur à 0.")
        return redirect("cotisationtontine:initier_versement", member_id=member_id)

    # Forcer l’entier (XOF)
    montant = montant.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    # 5) Charger config PayDunya (+ headers/base_url) et vérifier la cohérence mode/clefs
    try:
        cfg = _paydunya_conf()
        headers = _paydunya_headers(cfg)
        base_url = _paydunya_base_url(cfg)
    except RuntimeError as e:
        messages.error(request, str(e))
        return redirect("cotisationtontine:initier_versement", member_id=member_id)

    mode = (cfg.get("env") or cfg.get("mode") or "").lower()
    has_test_tokens = any(
        "test_" in (cfg.get(k, "") or "").lower()
        for k in ("public_key", "private_key", "token")
    )
    if mode in ("prod", "production", "live") and has_test_tokens:
        messages.error(request, "Clés TEST détectées alors que l'API LIVE est sélectionnée.")
        return redirect("cotisationtontine:group_detail", group_id=group_id)
    # (Optionnel) Bloquer l'inverse :
    # if mode in ("", "sandbox") and not has_test_tokens:
    #     messages.error(request, "Clés LIVE détectées alors que l'API SANDBOX est sélectionnée.")
    #     return redirect("cotisationtontine:group_detail", group_id=group_id)

    # 6) Frais : 2% + 50 FCFA
    frais_total = (montant * Decimal("0.02") + Decimal("50")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    montant_total = (montant + frais_total).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    # 7) URLs
    callback_url = request.build_absolute_uri(reverse("cotisationtontine:versement_callback"))
    return_url = request.build_absolute_uri(reverse("cotisationtontine:versement_merci")) + f"?group_id={group_id}"
    cancel_url = request.build_absolute_uri(reverse("cotisationtontine:group_detail", args=[group_id]))

    # 8) Payload PayDunya
    payload = {
        "invoice": {
            "items": [
                {
                    "name": "Versement épargne",
                    "quantity": 1,
                    "unit_price": _as_fcfa_int(montant_total),
                    "total_price": _as_fcfa_int(montant_total),
                    "description": (
                        f"Versement membre {getattr(member.user, 'nom', None) or member.user.phone} "
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
        "actions": {
            "callback_url": callback_url,
            "return_url": return_url,
            "cancel_url": cancel_url,
        },
        "custom_data": {
            "member_id": member.id,
            "user_id": request.user.id,
            "montant": _as_fcfa_int(montant),   # hors frais
            "frais": _as_fcfa_int(frais_total),
            "methode": methode,
            "group_id": group_id,
        },
    }

    # 9) Création de la facture
    try:
        resp = requests.post(f"{base_url}/checkout-invoice/create", headers=headers, json=payload, timeout=20)
    except requests.exceptions.RequestException as e:
        messages.error(request, f"Erreur réseau PayDunya : {e}")
        return redirect("cotisationtontine:initier_versement", member_id=member_id)

    if resp.status_code != 200:
        txt = resp.text[:800] if resp.text else ""
        messages.error(request, f"Erreur PayDunya (HTTP {resp.status_code}).")
        if settings.DEBUG and txt:
            messages.info(request, f"DEBUG PayDunya: {txt}")
        return redirect("cotisationtontine:initier_versement", member_id=member_id)

    # 10) Parsing JSON
    try:
        data = resp.json()
    except json.JSONDecodeError:
        messages.error(request, "Réponse PayDunya invalide (JSON).")
        if settings.DEBUG:
            messages.info(request, f"DEBUG PayDunya: {resp.text[:800]}")
        return redirect("cotisationtontine:initier_versement", member_id=member_id)

    if settings.DEBUG:
        try:
            messages.info(request, f"DEBUG PayDunya: {json.dumps(data)[:800]}")
        except Exception:
            pass

    # 11) Succès ?
    if isinstance(data, dict) and data.get("response_code") == "00":
        invoice_url = None
        rt = data.get("response_text")

        # a) URL directe
        if isinstance(rt, str) and rt.startswith("http"):
            invoice_url = rt
        # b) Dictionnaire
        elif isinstance(rt, dict):
            invoice_url = rt.get("invoice_url") or rt.get("checkout_url")

        # c) Fallbacks fréquents
        if not invoice_url:
            invoice_url = (
                data.get("invoice_url")
                or data.get("checkout_url")
                or data.get("url")
                or (data.get("data", {}).get("invoice_url") if isinstance(data.get("data"), dict) else None)
            )

        if invoice_url:
            return redirect(invoice_url)

        # d) Pas d'URL mais token => on laisse le callback finaliser
        token = data.get("token") or (rt.get("token") if isinstance(rt, dict) else None)
        if token:
            messages.warning(request, "Facture créée. Redirection indisponible ; finalisez le paiement sur PayDunya.")
            return redirect("cotisationtontine:group_detail", group_id=group_id)

        messages.warning(request, "Facture créée mais URL manquante. Retour au groupe.")
        return redirect("cotisationtontine:group_detail", group_id=group_id)

    # 12) Erreur métier PayDunya
    err_text = data.get("response_text", "Erreur inconnue")
    code = data.get("response_code")

    if code == "1001":
        messages.error(request, "Échec de création: MasterKey invalide. Vérifiez PAYDUNYA_MASTER_KEY et le mode (test/live).")
    else:
        messages.error(request, f"Échec de création de facture: {err_text}")

    if settings.DEBUG:
        try:
            messages.info(request, f"DEBUG PayDunya: {json.dumps(data)[:800]}")
        except Exception:
            pass

    return redirect("cotisationtontine:initier_versement", member_id=member_id)


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
        cfg = _paydunya_conf()
        headers = _paydunya_headers(cfg)
        base_url = _paydunya_base_url(cfg)
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
from django.urls import reverse, NoReverseMatch
from django.views.decorators.http import require_GET

def _safe_reverse(candidates):
    for name, args, kwargs in candidates:
        try:
            return reverse(name, args=args or None, kwargs=kwargs or None)
        except NoReverseMatch:
            continue
    return "/"

@require_GET
def versement_merci(request: HttpRequest) -> HttpResponse:
    token = request.GET.get("token") or ""
    group_id = request.GET.get("group_id")

    # back_url intelligent
    candidates = []
    if group_id:
        candidates.append(("cotisationtontine:group_detail", [group_id], {}))
    candidates.append(("cotisationtontine:group_list", [], {}))
    candidates.append(("epargnecredit:group_list", [], {}))
    candidates.append(("landing:home", [], {}))
    candidates.append(("home", [], {}))
    back_url = _safe_reverse(candidates)

    # Construire un lien "ouvrir la facture" si utile (sandbox vs live)
    invoice_url = ""
    if token:
        invoice_url = (
            f"https://paydunya.com/sandbox-checkout/invoice/{token}"
            if (getattr(settings, "PAYDUNYA", {}).get("sandbox", True))
            else f"https://paydunya.com/checkout/invoice/{token}"
        )

    # Confirmer l’état auprès de PayDunya
    status = "unknown"   # paid | pending | failed | unknown | error
    created_fallback = False
    conf = {}

    if token:
        try:
            cfg = _paydunya_conf()
            headers = _paydunya_headers(cfg)
            base_url = _paydunya_base_url(cfg)
        except RuntimeError:
            # settings mal configurés
            return render(request, "cotisationtontine/versement_merci.html", {
                "token": token,
                "back_url": back_url,
                "invoice_url": invoice_url,
                "status": "error",
                "created_fallback": False,
            })

        try:
            r = requests.get(f"{base_url}/checkout-invoice/confirm/{token}", headers=headers, timeout=20)
            if r.status_code == 200:
                conf = r.json()
                code_ok = (conf.get("response_code") == "00")
                st = str(conf.get("status", "")).lower()
                if code_ok and st in {"completed", "paid", "accepted"}:
                    status = "paid"
                    # Si le callback n’a pas encore créé l’écriture (ex: serveur local),
                    # on peut (optionnel) créer en DEV uniquement.
                    if not Versement.objects.filter(transaction_id=token).exists() and settings.DEBUG:
                        custom = conf.get("custom_data") if isinstance(conf.get("custom_data"), dict) else {}
                        try:
                            member_id = int(custom.get("member_id", 0))
                        except Exception:
                            member_id = 0
                        member = GroupMember.objects.filter(id=member_id).select_related("group", "user").first()
                        if member:
                            try:
                                from decimal import Decimal, ROUND_HALF_UP
                                montant = Decimal(str(custom.get("montant", "0"))).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
                                frais = Decimal(str(custom.get("frais", "0"))).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
                            except Exception:
                                montant, frais = Decimal("0"), Decimal("0")
                            Versement.objects.create(
                                transaction_id=token,
                                member=member,
                                montant=montant,
                                frais=frais,
                                methode="PAYDUNYA",
                            )
                            created_fallback = True
                elif code_ok and st in {"pending", "new"}:
                    status = "pending"
                elif st in {"cancelled", "canceled", "failed"}:
                    status = "failed"
                else:
                    status = st or "unknown"
            else:
                status = "error"
        except requests.exceptions.RequestException:
            status = "error"

    return render(request, "cotisationtontine/versement_merci.html", {
        "token": token,
        "back_url": back_url,
        "invoice_url": invoice_url,
        "status": status,
        "created_fallback": created_fallback,
        # "conf": conf,  # décommente en DEBUG si tu veux afficher brut
    })



def editer_membre_view(request, group_id, membre_id):
    return HttpResponse(f"Éditer membre {membre_id} du groupe {group_id}")

def supprimer_membre_view(request, group_id, membre_id):
    return HttpResponse(f"Supprimer membre {membre_id} du groupe {group_id}")


def reset_cycle_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    # Ici tu réinitialises les versements/crédits selon ta logique
    messages.info(request, f"Cycle réinitialisé pour le groupe {group.nom} (à implémenter).")
    return redirect("cotisationtontine:group_detail", group_id=group.id)

from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.db import transaction
import random
from cotisationtontine.models import Group, Tirage, GroupMember

@login_required
def tirage_au_sort_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    # ✅ Vérifier que seul l'admin ou un superuser peut tirer au sort
    if request.user != group.admin and not request.user.is_superuser:
        return render(request, '403.html', status=403)

    def membres_eligibles_pour_tirage(group):
        membres = list(group.membres.filter(actif=True, exit_liste=False))
        total = len(membres)

        if total <= 1:
            return membres  # tout le monde éligible

        # Exclure le prochain gagnant s'il est défini et qu'il reste plus de 2 membres
        if group.prochain_gagnant and total > 2:
            membres = [m for m in membres if m.id != group.prochain_gagnant.id]

        return membres

    membres_eligibles = membres_eligibles_pour_tirage(group)

    gagnant = None
    montant_total = 0

    if membres_eligibles:
        gagnant = random.choice(membres_eligibles)

        # 💡 Si c'est le premier tirage, on fixe le montant pour tous les gagnants
        if group.montant_fixe_gagnant is None:
            montant_total = group.montant_base * group.membres.filter(actif=True, exit_liste=False).count()
            group.montant_fixe_gagnant = montant_total
            group.save()
        else:
            montant_total = group.montant_fixe_gagnant

        with transaction.atomic():
            # Enregistrer le tirage
            Tirage.objects.create(
                group=group,
                gagnant=gagnant,
                membre=gagnant,
                montant=montant_total,
            )

            # Déterminer le prochain gagnant à ignorer
            total_apres_tirage = group.membres.filter(actif=True, exit_liste=False).count() - 1
            if total_apres_tirage > 2:
                group.prochain_gagnant = gagnant
            else:
                group.prochain_gagnant = None
            group.save()

    context = {
        'group': group,
        'gagnant': gagnant,
        'montant_total': montant_total,
    }
    return render(request, 'cotisationtontine/tirage_resultat.html', context)

# cotisationtontine/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.urls import reverse
from django.apps import apps

from .models import Group, GroupMember, CotisationTontine, Tirage, TirageHistorique
# Si Versement est dans l’app cotisationtontine, importe-le si nécessaire pour d’autres vues
# from .models import Versement


# ============================================================
# Réinitialisation d’un cycle de tontine (fusion + durcissement)
# ============================================================
@login_required
@transaction.atomic
def reset_cycle_view(request, group_id):
    """
    Réinitialise le cycle d’un groupe :
      - Permissions : admin du groupe ou superuser/super_admin.
      - GET : page de confirmation (avec rappel des membres non gagnants).
      - POST :
          * Archive les tirages en cours -> TirageHistorique
          * Supprime tirages actifs et cotisations du cycle
          * Met à jour group.date_reset (+ cycle_en_cours=True si présent)
      - NE SUPPRIME PAS les Versement (traçabilité).
    """
    group = get_object_or_404(Group, id=group_id)

    user = request.user
    is_group_admin = (user == getattr(group, "admin", None))
    is_superuser = getattr(user, "is_superuser", False) or getattr(user, "is_super_admin", False)
    if not (is_group_admin or is_superuser):
        messages.error(request, "Seul l’administrateur du groupe ou un superutilisateur peut réinitialiser le cycle.")
        return redirect("cotisationtontine:group_detail", group_id=group.id)

    # Prépare l’info des non-gagnants (utilisée en GET et vérifiée en POST)
    membres = list(group.membres.select_related("user").all())  # GroupMember
    gagnants_actuels = {t.gagnant for t in group.tirages.select_related("gagnant").all() if t.gagnant}
    gagnants_historiques = {t.gagnant for t in group.tirages_historiques.select_related("gagnant").all() if t.gagnant}
    tous_les_gagnants = gagnants_actuels.union(gagnants_historiques)
    membres_non_gagnants = [m for m in membres if m not in tous_les_gagnants]

    if request.method != "POST":
        return render(
            request,
            "cotisationtontine/confirm_reset_cycle.html",
            {
                "group": group,
                "membres_non_gagnants": membres_non_gagnants,
                "nb_tirages_actuels": group.tirages.count(),
                "nb_tirages_historiques": group.tirages_historiques.count(),
                "date_reset_precedent": getattr(group, "date_reset", None),
            },
        )

    # En POST : si certains membres n’ont pas gagné, on avertit et on sort
    if membres_non_gagnants:
        noms = ", ".join(getattr(m.user, "nom", None) or getattr(m.user, "username", "") or str(m.user_id) for m in membres_non_gagnants)
        messages.warning(request, f"Les membres suivants n’ont pas encore gagné : {noms}.")
        return redirect("cotisationtontine:group_detail", group_id=group.id)

    # 1) Archiver les tirages en cours -> TirageHistorique
    tirages_actuels = list(group.tirages.select_related("gagnant").all())
    if tirages_actuels:
        TirageHistorique.objects.bulk_create(
            [
                TirageHistorique(
                    group=group,
                    gagnant=t.gagnant,
                    montant=t.montant,
                    date_tirage=t.date_tirage or timezone.now(),
                )
                for t in tirages_actuels
            ]
        )

    # 2) Supprimer les tirages en cours
    if tirages_actuels:
        group.tirages.all().delete()

    # 3) Supprimer les cotisations du cycle (on laisse les Versement pour l’audit)
    CotisationTontine.objects.filter(member__group=group).delete()

    # 4) Mettre à jour le groupe
    group.date_reset = timezone.now()
    if hasattr(group, "cycle_en_cours"):
        group.cycle_en_cours = True
    group.save(update_fields=["date_reset"] + (["cycle_en_cours"] if hasattr(group, "cycle_en_cours") else []))

    messages.success(request, f"✅ Cycle du groupe « {getattr(group, 'nom', group.id)} » réinitialisé avec succès. Les versements peuvent reprendre.")
    return redirect("cotisationtontine:group_detail", group_id=group.id)


# =====================
# Résultats d’un tirage
# =====================
@login_required
def tirage_resultat_view(request, group_id):
    """
    Affiche une page de résultats (à compléter selon ton besoin).
    """
    group = get_object_or_404(Group, id=group_id)
    # Ex : derniers tirages, prochain ordre, etc.
    tirages = group.tirages.select_related("gagnant__user").order_by("-date_tirage")
    return render(request, "cotisationtontine/tirage_resultat.html", {"group": group, "tirages": tirages})


# ==================================
# Historique des cycles (si disponible)
# ==================================
@login_required
def historique_cycles_view(request, group_id):
    """
    Affiche l'historique des cycles passés d'un groupe si le modèle Cycle existe.
    Tolérant : si le modèle n’existe pas, on rend une page vide (sans 500).
    """
    group = get_object_or_404(Group, id=group_id)

    # Récupère Cycle dynamiquement pour éviter un crash si non migré/commenté
    try:
        Cycle = apps.get_model("cotisationtontine", "Cycle")
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
        "cotisationtontine/historique_cycles.html",
        {
            "group": group,
            "anciens_cycles": anciens_cycles,
        },
    )

import logging
import json
from decimal import Decimal, ROUND_HALF_UP

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from .models import Group, Tirage, PaiementGagnant

# Helpers PayDunya (importés depuis ton module utilitaire)
from .paydunya_utils import (
    paydunya_conf as _paydunya_conf,
    paydunya_headers as _paydunya_headers,
    paydunya_base_url as _paydunya_base_url,
    as_fcfa_int as _as_fcfa_int,
)

logger = logging.getLogger(__name__)


@login_required
def payer_gagnant(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    # 1) Récupérer le dernier tirage gagnant
    dernier_tirage = (
        Tirage.objects.filter(group=group).order_by("-date_tirage").first()
    )
    if not dernier_tirage or not dernier_tirage.gagnant:
        messages.error(request, "Aucun gagnant défini pour ce groupe.")
        return redirect("group_detail", group_id=group.id)

    gagnant = dernier_tirage.gagnant

    # 2) Montant total (fixe si défini, sinon = montant_base * nb_membres_actifs)
    try:
        if group.montant_fixe_gagnant is not None:
            montant_total = Decimal(str(group.montant_fixe_gagnant))
        else:
            nb_actifs = group.membres.filter(actif=True, exit_liste=False).count()
            montant_total = Decimal(str(group.montant_base)) * Decimal(nb_actifs)
    except Exception:
        messages.error(request, "Montant du paiement invalide pour ce groupe.")
        return redirect("group_detail", group_id=group.id)

    if request.method == "POST":
        # 3) Frais : 2% + 50 FCFA (arrondi entier XOF)
        frais_total = (montant_total * Decimal("0.02") + Decimal("50")).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
        montant_total_avec_frais = (montant_total + frais_total).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )

        montant_total_int = _pay = _as_fcfa_int(montant_total)              # hors frais
        frais_total_int = _as_fcfa_int(frais_total)
        montant_total_avec_frais_int = _as_fcfa_int(montant_total_avec_frais)

        # 4) Base URL publique pour callback/return (ngrok en dev si dispo)
        if settings.DEBUG and getattr(settings, "NGROK_BASE_URL", None):
            site_base = settings.NGROK_BASE_URL.rstrip("/") + "/"
        else:
            site_base = request.build_absolute_uri("/")

        # 5) Charge config PayDunya + headers + endpoint
        try:
            cfg = _paydunya_conf()
            headers = _paydunya_headers(cfg)
            api_base = _paydunya_base_url(cfg)
        except RuntimeError as e:
            messages.error(request, str(e))
            return redirect("group_detail", group_id=group.id)

        # 6) (option) Cohérence mode/clefs
        mode = (cfg.get("env") or cfg.get("mode") or "").lower()
        has_test_tokens = any(
            "test_" in (cfg.get(k, "") or "").lower()
            for k in ("public_key", "private_key", "token")
        )
        if mode in ("prod", "production", "live") and has_test_tokens:
            messages.error(
                request, "Clés TEST détectées alors que l'API LIVE est sélectionnée."
            )
            return redirect("group_detail", group_id=group.id)

        # 7) Payload PayDunya — structure standard (invoice/store/actions/custom_data)
        payload = {
            "invoice": {
                "items": [
                    {
                        "name": "Paiement gagnant Tontine",
                        "quantity": 1,
                        "unit_price": montant_total_avec_frais_int,
                        "total_price": montant_total_avec_frais_int,
                        "description": (
                            f"Paiement {getattr(gagnant.user, 'nom', None) or gagnant.user.phone} "
                            f"- Frais {frais_total_int} FCFA"
                        ),
                    }
                ],
                "description": f"Versement gagnant (+{frais_total_int} FCFA de frais)",
                "total_amount": montant_total_avec_frais_int,
                "currency": "XOF",
            },
            "store": {
                "name": cfg.get("store_name", "YaayESS"),
                "tagline": cfg.get("store_tagline", "Plateforme de gestion financière"),
                "website_url": cfg.get("website_url", "https://yaayess.com"),
            },
            "actions": {
                "callback_url": f"{site_base}cotisationtontine/paiement_gagnant/callback/",
                "return_url": f"{site_base}cotisationtontine/paiement_gagnant/merci/",
                "cancel_url": f"{site_base}cotisationtontine/groupe/{group.id}/",  # adapte si besoin
            },
            "custom_data": {
                "group_id": group.id,
                "gagnant_id": gagnant.id,
                "montant_saisi": montant_total_int,  # hors frais
                "frais_total": frais_total_int,
            },
        }

        # 8) Appel API
        try:
            logger.info("⏳ Envoi requête PayDunya...")
            resp = requests.post(
                f"{api_base}/checkout-invoice/create",
                headers=headers,
                json=payload,
                timeout=20,
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur réseau PayDunya: {e}")
            messages.error(request, f"Erreur réseau PayDunya: {e}")
            return redirect("group_detail", group_id=group.id)

        logger.info(f"✅ Statut HTTP PayDunya : {resp.status_code}")

        if resp.status_code != 200:
            txt = (resp.text or "")[:800]
            messages.error(request, "Erreur PayDunya (HTTP).")
            if settings.DEBUG and txt:
                messages.info(request, f"DEBUG PayDunya: {txt}")
            return redirect("group_detail", group_id=group.id)

        # 9) JSON parsing + success handling
        try:
            data = resp.json()
        except json.JSONDecodeError:
            messages.error(request, "Réponse PayDunya invalide (JSON).")
            if settings.DEBUG:
                messages.info(request, f"DEBUG PayDunya: {(resp.text or '')[:800]}")
            return redirect("group_detail", group_id=group.id)

        if settings.DEBUG:
            try:
                logger.debug(f"🧾 Réponse JSON PayDunya : {json.dumps(data)[:800]}")
            except Exception:
                pass

        if isinstance(data, dict) and data.get("response_code") == "00":
            # extraire l'URL de redirection
            invoice_url = None
            rt = data.get("response_text")

            if isinstance(rt, str) and rt.startswith("http"):
                invoice_url = rt
            elif isinstance(rt, dict):
                invoice_url = rt.get("invoice_url") or rt.get("checkout_url")

            if not invoice_url:
                invoice_url = (
                    data.get("invoice_url")
                    or data.get("checkout_url")
                    or data.get("url")
                    or (
                        data.get("data", {}).get("invoice_url")
                        if isinstance(data.get("data"), dict)
                        else None
                    )
                )

            # Créer l'écriture locale EN_ATTENTE
            PaiementGagnant.objects.create(
                group=group,
                gagnant=gagnant,
                montant=montant_total,  # hors frais
                statut="EN_ATTENTE",
                transaction_id=data.get("token"),
                message="Paiement en attente validation PayDunya",
            )

            if invoice_url:
                return redirect(invoice_url)

            messages.warning(
                request,
                "Facture créée mais URL manquante. Retour au groupe.",
            )
            return redirect("group_detail", group_id=group.id)

        # Erreur PayDunya (métier)
        err_text = data.get("response_text", "Erreur inconnue")
        code = data.get("response_code")
        if code == "1001":
            messages.error(
                request,
                "Échec création: MasterKey invalide. Vérifiez PAYDUNYA_MASTER_KEY et le mode (test/live).",
            )
        else:
            messages.error(request, f"Échec création paiement : {err_text}")

        return redirect("group_detail", group_id=group.id)

    # GET — affichage
    return render(
        request,
        "cotisationtontine/payer_gagnant.html",
        {"group": group, "gagnant": gagnant, "montant_total": montant_total},
    )


@csrf_exempt  # PayDunya n'envoie pas de CSRF token
def paiement_gagnant_callback(request):
    if request.method != "POST":
        return JsonResponse({"error": "Méthode non autorisée"}, status=405)

    # Accepter JSON ou x-www-form-urlencoded
    try:
        if request.content_type and "application/json" in request.content_type:
            data = json.loads(request.body or b"{}")
        else:
            data = request.POST.dict()
    except json.JSONDecodeError:
        logger.error("Corps JSON invalide dans callback PayDunya")
        return JsonResponse({"error": "JSON invalide"}, status=400)
    except Exception as e:
        logger.error(f"Erreur parse callback: {e}")
        return JsonResponse({"error": "Erreur serveur"}, status=500)

    logger.info(f"Callback PayDunya reçu: {json.dumps(data)}")

    token = data.get("token")
    status = data.get("status")                 # ex: "PAID" | "FAILED" ...
    response_code = data.get("response_code")   # ex: "00"
    response_text = data.get("response_text", "")

    if not token:
        return JsonResponse({"error": "Token manquant"}, status=400)

    paiement = PaiementGagnant.objects.filter(transaction_id=token).first()
    if not paiement:
        logger.error(f"PaiementGagnant introuvable pour token={token}")
        return JsonResponse({"error": "Paiement introuvable"}, status=404)

    # MAJ statut
    if response_code == "00" and (status or "").upper() in {"PAID", "SUCCESS", "SUCCEEDED"}:
        paiement.statut = "SUCCES"
    else:
        paiement.statut = "ECHEC"

    paiement.message = response_text
    paiement.save()

    logger.info(f"PaiementGagnant {token} mis à jour avec statut {paiement.statut}")
    return JsonResponse({"success": True})


def paiement_gagnant_merci(request):
    return render(request, "cotisationtontine/paiement_gagnant_merci.html")

from django.shortcuts import render
from .models import PaiementGagnant

def liste_paiements_gagnants(request):
    paiements = PaiementGagnant.objects.select_related('gagnant__user', 'group').order_by('-date_paiement')
    return render(request, 'cotisationtontine/paiement_gagnant.html', {
        'paiements': paiements
    })

# cotisationtontine/views.py

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

    return render(request, "cotisationtontine/historique_actions.html", {
        "logs": logs
    })


from django.db.models import Count


def membres_eligibles_pour_tirage(group):
    # Récupère le dernier tirage et son gagnant
    dernier_tirage = group.tirages.order_by('-date').first()  # adapte selon ton related_name
    membres = group.members.all()  # adapte selon ton related_name

    # Si le groupe a 1 membre ou moins, tous sont éligibles (pas d'exclusion)
    if membres.count() <= 1:
        return membres

    # Sinon, exclut le dernier gagnant du tirage
    if dernier_tirage:
        membres = membres.exclude(id=dernier_tirage.gagnant.id)

    return membres
