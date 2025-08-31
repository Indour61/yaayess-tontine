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
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta
from .models import Group, Versement, ActionLog


@login_required
def dashboard_epargne_credit(request):
    """
    Dashboard principal avec aperçu des groupes, activités récentes et statistiques.
    """

    # Groupes dont l'utilisateur est administrateur
    groupes_admin = Group.objects.filter(admin=request.user)

    # Groupes dont l'utilisateur est membre (via relation membres_ec)
    groupes_membre = Group.objects.filter(
        membres_ec=request.user
    ).exclude(admin=request.user).distinct()

    # Dernières actions de l'utilisateur
    dernieres_actions = ActionLog.objects.filter(user=request.user).order_by('-date')[:10]

    # Total des versements de l'utilisateur
    total_versements = Versement.objects.filter(
        member__user=request.user
    ).aggregate(total=Sum('montant'))['total'] or 0

    # Nombre total de groupes où l'utilisateur est membre
    total_groupes = groupes_membre.count() + groupes_admin.count()

    # Récupérer les versements récents (30 derniers jours)
    date_limite = timezone.now() - timedelta(days=30)
    versements_recents = Versement.objects.filter(
        member__user=request.user,
        date__gte=date_limite
    ).select_related('member__user', 'member__group').order_by('-date')[:5]

    # Statistiques des groupes administrés
    stats_groupes_admin = []
    for groupe in groupes_admin:
        total_membres = groupe.membres_ec.count()
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


@login_required
def group_detail(request, group_id):
    """
    Détails d'un groupe :
    - Liste des membres
    - Versements
    - Dernières actions
    - Invitation (si admin)
    """
    group = get_object_or_404(Group, id=group_id)

    # Vérification d'accès
    if not (
        group.admin == request.user or
        GroupMember.objects.filter(group=group, user=request.user).exists() or
        getattr(request.user, "is_super_admin", False)
    ):
        messages.error(request, "⚠️ Vous n'avez pas accès à ce groupe.")
        return redirect("epargnecredit:group_list")

    # Membres avec leurs infos
    membres = group.members.select_related('user')

    # Tous les versements liés à ce groupe
    versements = Versement.objects.filter(
        member__group=group
    ).select_related('member', 'member__user').order_by('date')

    # Montant total des versements du groupe
    total_montant = versements.aggregate(total=Sum('montant'))['total'] or 0

    # Total par membre
    versements_par_membre = versements.values('member').annotate(total_montant=Sum('montant'))
    montants_membres_dict = {v['member']: v['total_montant'] for v in versements_par_membre}

    # Dernier versement par membre
    dernier_versement_membres_dict = {}
    for membre in membres:
        dernier = versements.filter(member=membre).order_by('-date').first()
        dernier_versement_membres_dict[membre.id] = dernier
        # Ajouter le total au membre pour affichage
        membre.montant = montants_membres_dict.get(membre.id, 0)

    # Vérifier si l'utilisateur est admin du groupe ou super admin
    user_is_admin = (request.user == group.admin) or getattr(request.user, "is_super_admin", False)

    # Récupérer les 10 dernières actions liées à ce groupe
    actions = ActionLog.objects.filter(group=group).order_by('-date')[:10]

    # Générer le lien d'invitation
    invite_url = request.build_absolute_uri(
        reverse('accounts:inscription_et_rejoindre', args=[str(group.code_invitation)])
    )

    # Sauvegarder dans la session pour un accès rapide
    if user_is_admin:
        request.session['last_invitation_link'] = invite_url

    context = {
        'group': group,
        'membres': membres,
        'dernier_versement_membres_dict': dernier_versement_membres_dict,
        'total_montant': total_montant,
        'admin_user': group.admin,
        'actions': actions,
        'user_is_admin': user_is_admin,
        'invite_url': invite_url,
        'last_invitation_link': request.session.get('last_invitation_link'),
    }

    return render(request, 'epargnecredit/group_detail.html', context)

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

from epargnecredit.models import GroupMember, Versement


# ===============================
# Helpers PayDunya (compat PAYDUNYA / PAYDUNYA_KEYS)
# ===============================
def _pd_conf():
    """
    Récupère la configuration PayDunya depuis settings.
    Priorité à PAYDUNYA (recommandé), fallback vers PAYDUNYA_KEYS pour compat.
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
    # Recommande PAYDUNYA["sandbox"] True/False ; sinon bascule sur DEBUG.
    sandbox = cfg.get("sandbox", getattr(settings, "DEBUG", True)) if hasattr(cfg, "get") else getattr(settings, "DEBUG", True)
    return "https://app.paydunya.com/sandbox-api/v1" if sandbox else "https://app.paydunya.com/api/v1"


def _as_fcfa_int(amount: Decimal) -> int:
    """PayDunya attend des entiers (FCFA)."""
    return int(amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


# ===============================
# Initier un versement
# ===============================
@login_required
@transaction.atomic
def initier_versement(request: HttpRequest, member_id: int) -> HttpResponse:
    """
    - CAISSE : crée directement le Versement (pas de champ 'statut').
    - PAYDUNYA : crée la facture, redirige l’utilisateur, et attend le callback pour créer le Versement (idempotent).
    """
    member = get_object_or_404(GroupMember, id=member_id)
    group = member.group
    group_id = group.id

    # Permissions : soi-même, admin du groupe, ou super admin
    is_self = (request.user == member.user)
    is_group_admin = (request.user == getattr(group, "admin", None))
    is_super_admin = bool(getattr(request.user, "is_super_admin", False))
    if not (is_self or is_group_admin or is_super_admin):
        messages.error(request, "⚠️ Vous n'avez pas les droits pour effectuer un versement pour ce membre.")
        return redirect("epargnecredit:group_detail", group_id=group_id)

    if request.method == "GET":
        return render(request, "epargnecredit/initier_versement.html", {"member": member, "group": group})

    # --- POST ---
    montant_raw = (request.POST.get("montant") or "").replace(",", ".").strip()
    methode = (request.POST.get("methode") or "paydunya").lower()

    # Validation montant
    try:
        montant = Decimal(montant_raw)
    except Exception:
        messages.error(request, "Montant invalide.")
        return redirect("epargnecredit:initier_versement", member_id=member_id)

    if montant <= 0:
        messages.error(request, "Le montant doit être supérieur à 0.")
        return redirect("epargnecredit:initier_versement", member_id=member_id)

    # Forcer FCFA entier
    montant = montant.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    # 1) CAISSE -> écriture immédiate (⚠️ pas de champ 'statut')
    if methode == "caisse":
        Versement.objects.create(
            member=member,
            montant=montant,
            frais=Decimal("0"),
            methode="CAISSE",
            transaction_id=f"CAISSE-{member.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
        )
        messages.success(request, f"✅ Versement de {_as_fcfa_int(montant)} FCFA enregistré via Caisse.")
        return redirect("epargnecredit:group_detail", group_id=group_id)

    # 2) PAYDUNYA
    try:
        cfg = _pd_conf()
        headers = _pd_headers(cfg)
        base_url = _pd_base_url(cfg)
    except RuntimeError as e:
        messages.error(request, str(e))
        return redirect("epargnecredit:initier_versement", member_id=member_id)

    # Frais : 2% + 50 FCFA (arrondi FCFA)
    frais_total = (montant * Decimal("0.02") + Decimal("50")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    montant_total = (montant + frais_total).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    # URLs absolues
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
                    "description": f"Versement membre {member.user.nom or member.user.phone} (frais: {_as_fcfa_int(frais_total)} FCFA)",
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
        "actions": {  # ✅ bon emplacement pour les URLs
            "callback_url": callback_url,
            "return_url": return_url,
            "cancel_url": cancel_url,
        },
        # Données utiles au callback
        "custom_data": {
            "member_id": member.id,
            "user_id": request.user.id,
            "montant": _as_fcfa_int(montant),  # hors frais
            "frais": _as_fcfa_int(frais_total),
        },
    }

    # Créer la facture
    try:
        resp = requests.post(f"{base_url}/checkout-invoice/create", headers=headers, json=payload, timeout=20)
    except requests.exceptions.RequestException as e:
        messages.error(request, f"Erreur réseau PayDunya : {e}")
        return redirect("epargnecredit:initier_versement", member_id=member_id)

    if resp.status_code != 200:
        messages.error(request, f"Erreur PayDunya (HTTP {resp.status_code})")
        if getattr(settings, "DEBUG", False):
            messages.info(request, f"DEBUG PayDunya: {resp.text[:600]}")
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

    # --- Extraction/redirect (gère response_text = URL string) ---
    if isinstance(data, dict) and data.get("response_code") == "00":
        invoice_url = None
        rt = data.get("response_text")

        # Cas principal: PayDunya renvoie l'URL directement en string
        if isinstance(rt, str) and rt.startswith("http"):
            invoice_url = rt
        # Variante: dict {invoice_url: ...}
        elif isinstance(rt, dict):
            invoice_url = rt.get("invoice_url")

        # Fallbacks communs
        if not invoice_url:
            invoice_url = (
                data.get("invoice_url")
                or data.get("checkout_url")
                or data.get("url")
                or (data.get("data", {}).get("invoice_url") if isinstance(data.get("data"), dict) else None)
            )

        if invoice_url:
            return redirect(invoice_url)

        token = data.get("token") or (rt.get("token") if isinstance(rt, dict) else None)
        if token:
            messages.warning(request, "Facture créée. Redirection indisponible ; le paiement doit être finalisé côté PayDunya.")
            return redirect("epargnecredit:group_detail", group_id=group_id)

        messages.warning(request, "Facture créée mais URL manquante. Retour au groupe.")
        return redirect("epargnecredit:group_detail", group_id=group_id)

    messages.error(request, f"Échec de création de facture: {data.get('response_text', 'Erreur inconnue')}")
    return redirect("epargnecredit:initier_versement", member_id=member_id)


# ===============================
# Callback PayDunya (idempotent & confirm)
# ===============================
@csrf_exempt
@transaction.atomic
def versement_callback(request: HttpRequest) -> JsonResponse:
    """
    1) Récupère le token du payload
    2) Confirme auprès de PayDunya (endpoint confirm)
    3) Crée un Versement idempotent (transaction_id=token)
    """
    try:
        payload = json.loads(request.body or "{}")
    except Exception:
        return JsonResponse({"error": "Payload invalide"}, status=400)

    token = payload.get("token") or payload.get("payout_token") or payload.get("invoice", {}).get("token")
    if not token:
        return JsonResponse({"error": "Token manquant"}, status=400)

    # Idempotence : si déjà traité, OK
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

    # Récupération des custom_data (du confirm si présents, sinon du payload)
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
    Versement.objects.get_or_create(
        transaction_id=token,
        defaults={
            "member": member,
            "montant": montant,
            "frais": frais,
            "methode": "PAYDUNYA",
        },
    )

    return JsonResponse({"message": "✅ Versement confirmé"}, status=200)


# ===============================
# Page de remerciement
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


