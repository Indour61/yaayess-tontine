from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils import timezone
from django.db import IntegrityError
from django.core.exceptions import ValidationError

from .forms import CustomUserCreationForm, CustomAuthenticationForm
from cotisationtontine.models import Group, GroupMember

from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.db import transaction, IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.urls import reverse
from accounts.forms import CustomUserCreationForm, CustomAuthenticationForm
from accounts.models import CustomUser
from cotisationtontine.models import Group, GroupMember


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.db import transaction
from django.urls import reverse
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from .models import CustomUser
from epargnecredit.models import Group, GroupMember

# ----------------------------------------------------
# Vue d'inscription
# ----------------------------------------------------
@transaction.atomic
def signup_view(request):
    """
    Création d'un compte CustomUser avec champ 'option'.
    - Si 'group_id' dans GET ou POST : ajout automatique au groupe (invitation)
    - Redirection vers le dashboard correspondant à l'option choisie
    """
    if request.user.is_authenticated:
        messages.info(request, "Vous êtes déjà connecté.")
        if request.user.option == '1':
            return redirect('cotisationtontine:dashboard_tontine_simple')
        else:
            return redirect('epargnecredit:dashboard_epargne_credit')

    group_id = request.GET.get('group_id') or request.POST.get('group_id')
    group = get_object_or_404(Group, id=group_id) if group_id else None

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()

                # Connexion automatique
                login(request, user)

                # Ajout automatique au groupe si fourni
                if group:
                    _, created = GroupMember.objects.get_or_create(
                        group=group,
                        user=user,
                        defaults={'date_joined': timezone.now()}
                    )
                    if created:
                        messages.success(request, f"Vous avez été ajouté au groupe {group.nom}.")
                    else:
                        messages.info(request, f"Vous êtes déjà membre du groupe {group.nom}.")

                messages.success(request, f"Bienvenue {user.nom} ! Votre compte a été créé.")

                # Redirection selon l'option
                if user.option == '1':
                    return redirect(
                        reverse('cotisationtontine:group_detail', args=[group.id])
                    ) if group else redirect('cotisationtontine:dashboard_tontine_simple')
                else:
                    return redirect('epargnecredit:dashboard_epargne_credit')

            except Exception as e:
                messages.error(request, f"Erreur lors de la création du compte : {str(e)}")
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = CustomUserCreationForm()

    return render(request, "accounts/signup.html", {"form": form, "group": group})

# ----------------------------------------------------
# Vue de connexion
# ----------------------------------------------------
def login_view(request):
    """
    Connexion avec validation de l'option.
    - Redirection vers le dashboard selon l'option
    - Si utilisateur membre d'un groupe, redirection vers ce groupe
    """
    if request.user.is_authenticated:
        messages.info(request, "Vous êtes déjà connecté.")
        if request.user.option == '1':
            member = GroupMember.objects.filter(user=request.user).first()
            return redirect(
                reverse("cotisationtontine:group_detail", args=[member.group.id])
            ) if member else redirect("cotisationtontine:dashboard_tontine_simple")
        else:
            return redirect("epargnecredit:dashboard_epargne_credit")

    if request.method == "POST":
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Connexion réussie. Bienvenue {user.nom} !")

            # Redirection selon l'option
            if user.option == '1':
                member = GroupMember.objects.filter(user=user).first()
                return redirect(
                    reverse("cotisationtontine:group_detail", args=[member.group.id])
                ) if member else redirect("cotisationtontine:dashboard_tontine_simple")
            else:
                return redirect("epargnecredit:dashboard_epargne_credit")
        else:
            messages.error(request, "Numéro/nom ou mot de passe incorrect, ou option invalide.")
    else:
        form = CustomAuthenticationForm()

    return render(request, "accounts/login.html", {"form": form})

@login_required
def logout_view(request):
    """
    Déconnecte l'utilisateur et redirige vers la page de connexion.
    """
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('accounts:login')

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.db import transaction

from .models import CustomUser


@login_required
@transaction.atomic
def profile_view(request):
    """
    Affiche et permet de modifier le profil de l'utilisateur connecté.
    """
    user = request.user

    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()

        modifications = False

        # 🔹 Vérification du nom
        if nom and nom != user.nom:
            if CustomUser.objects.filter(nom=nom).exclude(id=user.id).exists():
                messages.error(request, "❌ Ce nom est déjà utilisé par un autre utilisateur.")
            else:
                user.nom = nom
                modifications = True
                messages.success(request, "✅ Votre nom a été mis à jour.")

        # 🔹 Vérification de l'email
        if email and email != user.email:
            if CustomUser.objects.filter(email=email).exclude(id=user.id).exists():
                messages.error(request, "❌ Cet email est déjà utilisé par un autre utilisateur.")
            else:
                user.email = email
                modifications = True
                messages.success(request, "✅ Votre email a été mis à jour.")

        # 🔹 Vérification du téléphone
        if phone and phone != user.phone:
            if CustomUser.objects.filter(phone=phone).exclude(id=user.id).exists():
                messages.error(request, "❌ Ce numéro de téléphone est déjà utilisé par un autre utilisateur.")
            else:
                user.phone = phone
                modifications = True
                messages.success(request, "✅ Votre numéro de téléphone a été mis à jour.")

        # 🔹 Sauvegarde si nécessaire
        if modifications:
            user.save()
        else:
            messages.info(request, "ℹ️ Aucune modification détectée.")

        return redirect('accounts:profile')

    # 🔹 En GET, affiche le profil avec les données actuelles
    context = {
        "user": user
    }
    return render(request, 'accounts/profile.html', context)


from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import CustomAuthenticationForm, CustomUserCreationForm
# IMPORTANT : utilisez le Group/GroupMember de l'app Tontine (où se fait l'invitation)
from cotisationtontine.models import Group, GroupMember

import random
import string

User = get_user_model()


# ----------------------------------------------------
# Helpers
# ----------------------------------------------------

def _generate_alias(base_name: str) -> str:
    """Génère un alias unique basé sur le nom + 4 chiffres."""
    base = base_name.strip().lower().replace(" ", ".")
    suffix = "".join(random.choices(string.digits, k=4))
    return f"{base}.{suffix}"


def _unique_alias_for(name: str) -> str:
    alias = _generate_alias(name)
    while User.objects.filter(alias=alias).exists():
        alias = _generate_alias(name)
    return alias



from django.core.exceptions import PermissionDenied

def admin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied
        # Vérifie si l'utilisateur est admin dans un groupe
        is_admin = GroupMember.objects.filter(user=request.user, role='ADMIN').exists()
        if not (request.user.is_super_admin or is_admin):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped_view

from accounts.decorators import admin_required, membre_required

@admin_required
def dashboard_admin(request):
    # vue réservée à l'admin
    ...

@membre_required
def dashboard_membre(request):
    # vue réservée aux membres
    ...

# --- Imports nécessaires (au besoin, complète/évite les doublons) ---
from django.apps import apps
from django.db.models import Q
from django.http import Http404

# ---------- Helpers de recherche ----------
def _get_field_names(Model) -> set:
    return {f.name for f in Model._meta.get_fields()}

def _find_group_in_model(Model, code: str):
    """
    Cherche un Group dans Model en testant plusieurs champs possibles.
    Utilise filter().first() pour éviter MultipleObjectsReturned.
    """
    if not Model or not code:
        return None
    fields = _get_field_names(Model)
    q = Q()
    for field in ("code_invitation", "invitation_code", "uuid", "code", "slug"):
        if field in fields:
            q |= Q(**{field: code})
    obj = Model.objects.filter(q).order_by("-id").first() if q else None
    if obj:
        return obj
    if code.isdigit() and "id" in fields:
        return Model.objects.filter(id=int(code)).first()
    return None

def _resolve_group_by_code(code: str):
    """
    Recherche un Group par code dans:
      1) cotisationtontine.Group
      2) epargnecredit.Group
      3) via Invitation.* -> group (accounts / cotisationtontine / epargnecredit)
    Lève Http404 si rien n'est trouvé.
    """
    code = (code or "").strip()
    if not code:
        raise Http404("Invitation ou groupe introuvable.")

    # 1) Cherche directement dans les modèles Group
    for app_label in ("cotisationtontine", "epargnecredit"):
        try:
            GroupModel = apps.get_model(app_label, "Group")
        except LookupError:
            GroupModel = None
        g = _find_group_in_model(GroupModel, code) if GroupModel else None
        if g:
            return g

    # 2) Cherche via les modèles Invitation possédant un FK 'group'
    for app_label in ("accounts", "cotisationtontine", "epargnecredit"):
        try:
            Invitation = apps.get_model(app_label, "Invitation")
        except LookupError:
            Invitation = None
        if not Invitation:
            continue

        fields = _get_field_names(Invitation)
        q = Q()
        if "code" in fields:
            q |= Q(code=code)
        if "token" in fields:
            q |= Q(token=code)  # string vers UUID fonctionne, Django castera
        if "uuid" in fields:
            q |= Q(uuid=code)

        if q:
            inv = (
                Invitation.objects.select_related("group")
                .filter(q)
                .order_by("-id")
                .first()
            )
            if inv and getattr(inv, "group", None):
                return inv.group

    # 3) Rien trouvé
    raise Http404("Invitation ou groupe introuvable.")


from django.utils import timezone
from django.contrib import messages
from django.apps import apps

def _add_member_to_group(request, user, group) -> None:
    """
    Ajoute l'utilisateur au groupe (cotisationtontine ou epargnecredit) sans doublon.
    Utilise apps.get_model pour éviter les imports circulaires.
    Remplit quelques champs par défaut s'ils existent.
    """
    app_label = getattr(getattr(group, "_meta", None), "app_label", "")
    try:
        MemberModel = apps.get_model(app_label, "GroupMember")
    except LookupError:
        messages.error(request, "Type de groupe inconnu.")
        return

    # Prépare des valeurs par défaut seulement si les champs existent
    fields = {f.name for f in MemberModel._meta.get_fields()}
    defaults = {}
    if "montant" in fields:
        defaults["montant"] = 0
    if "date_joined" in fields:
        defaults["date_joined"] = timezone.now()
    if "actif" in fields:
        defaults["actif"] = True

    member, created = MemberModel.objects.get_or_create(
        group=group,
        user=user,
        defaults=defaults,
    )

    group_name = getattr(group, "nom", str(group.id))
    if created:
        messages.success(request, f"✅ Vous avez été ajouté au groupe « {group_name} ».")
    else:
        messages.info(request, f"ℹ️ Vous êtes déjà membre du groupe « {group_name} ».")




def _forced_option_for_group(group) -> str | None:
#def _forced_option_for_group(group) -> Optional[str]:
    """
    Retourne '1' si le groupe vient de cotisationtontine, '2' pour epargnecredit,
    sinon None si inconnu.
    """
    app_label = getattr(getattr(group, "_meta", None), "app_label", "")
    if app_label == "cotisationtontine":
        return "1"
    if app_label == "epargnecredit":
        return "2"
    return None


def _redirect_by_option(user: User, group=None) -> HttpResponse:
    """
    Redirige vers le bon dashboard / group_detail.
    - Si un groupe est fourni, on force l'option selon l'app du groupe (1 ou 2),
      on met à jour user.option si différent, puis on redirige vers le bon module.
    - Sinon, on retombe sur le comportement historique basé sur user.option.
    """
    forced = _forced_option_for_group(group) if group is not None else None
    option = forced or getattr(user, "option", None)

    # Synchroniser user.option si on a une option forcée
    if forced and getattr(user, "option", None) != forced:
        user.option = forced
        try:
            user.save(update_fields=["option"])
        except Exception:
            # fallback silencieux si le model n'a pas 'option'
            pass

    if option == "1":  # Cotisation & Tontine
        try:
            TMember = apps.get_model("cotisationtontine", "GroupMember")
            m = TMember.objects.filter(user=user).order_by("-id").first()
            if m:
                return redirect("cotisationtontine:group_detail", m.group.id)
        except Exception:
            pass
        return redirect("cotisationtontine:dashboard_tontine_simple")

    # Par défaut : Épargne & Crédit
    try:
        EMember = apps.get_model("epargnecredit", "GroupMember")
        m = EMember.objects.filter(user=user).order_by("-id").first()
        if m:
            return redirect("epargnecredit:group_detail", m.group.id)
    except Exception:
        pass
    return redirect("epargnecredit:dashboard_epargne_credit")

# optionnel mais bien: évite l’évaluation immédiate des annotations
#from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import authenticate, login, get_user_model
from django.http import Http404, HttpRequest, HttpResponse
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.db import transaction, IntegrityError

User = get_user_model()

# ✅ Constantes + libellés normalisés (accents corrigés)
OPTION_TONTINE = "1"
OPTION_EC = "2"
OPTION_LABELS = {
    OPTION_TONTINE: "Cotisation & Tontine",
    OPTION_EC: "Épargne & Crédit",
}

def _normalize_phone(raw: str) -> str:
    """Garde chiffres + éventuel + au début ; retire espaces et tirets."""
    s = (raw or "").strip().replace(" ", "").replace("-", "")
    if s.startswith("+"):
        return "+" + "".join(ch for ch in s[1:] if ch.isdigit())
    return "".join(ch for ch in s if ch.isdigit())

@ensure_csrf_cookie
@csrf_protect
@transaction.atomic
def inscription_et_rejoindre(request: HttpRequest, code: str) -> HttpResponse:
    """
    1) Retrouve le groupe depuis <code>
    2) Si l'utilisateur existe (phone), authentifie puis ajoute au groupe
    3) Sinon crée le compte (nom, phone, password), option forcée selon l'app d'origine
    4) Auto-valide si le lien vient de epargnecredit
    5) Redirige automatiquement vers le bon module (tontine ou epargne)
    """
    try:
        group = _resolve_group_by_code(code)
    except Http404:
        messages.error(request, "Lien d’invitation invalide ou expiré.")
        return render(
            request,
            "accounts/inscription_par_invit.html",
            {"group": None, "forced_option": None, "option_labels": OPTION_LABELS},
            status=404,
        )

    # Déterminer l’option (forcée) selon l’app du groupe
    forced_option = _forced_option_for_group(group)  # "1" (tontine) ou "2" (epargnecredit)
    is_ec_link = getattr(group._meta, "app_label", None) == "epargnecredit"

    if request.method == "GET":
        # Force cookie CSRF (utile si ouverture du lien dans un nouvel onglet)
        get_token(request)
        request.session["__csrf_touch__"] = timezone.now().isoformat()
        request.session.modified = True
        return render(
            request,
            "accounts/inscription_par_invit.html",
            {"group": group, "forced_option": forced_option, "option_labels": OPTION_LABELS},
        )

    # ----------- POST -----------
    nom = (request.POST.get("nom") or "").strip()
    phone = _normalize_phone(request.POST.get("phone"))
    password = (request.POST.get("password") or "").strip()
    confirm_password = (request.POST.get("confirm_password") or "").strip()

    # On ignore toute "option" libre si forced_option est défini
    option = forced_option or (request.POST.get("option") or "").strip()
    if option not in (OPTION_TONTINE, OPTION_EC):
        option = OPTION_TONTINE  # défaut sûr

    # Validations rapides
    if not all([nom, phone, password, confirm_password]):
        messages.error(request, "Tous les champs sont requis.")
        return render(
            request,
            "accounts/inscription_par_invit.html",
            {"group": group, "forced_option": forced_option, "option_labels": OPTION_LABELS},
            status=400,
        )

    if password != confirm_password:
        messages.error(request, "Les mots de passe ne correspondent pas.")
        return render(
            request,
            "accounts/inscription_par_invit.html",
            {"group": group, "forced_option": forced_option, "option_labels": OPTION_LABELS},
            status=400,
        )

    # Cas 1 : un compte existe déjà avec ce phone
    existing_by_phone = User.objects.filter(phone=phone).first()
    if existing_by_phone:
        user = authenticate(request, username=phone, password=password)
        if user is None:
            messages.error(request, "Mot de passe incorrect pour ce numéro de téléphone.")
            return render(
                request,
                "accounts/inscription_par_invit.html",
                {"group": group, "forced_option": forced_option, "option_labels": OPTION_LABELS},
                status=400,
            )

        # Prépare update ciblé
        fields_to_update = []

        # Mise à jour du nom si vide
        if not getattr(user, "nom", None):
            user.nom = nom
            fields_to_update.append("nom")

        # Synchroniser l'option avec celle du groupe du lien
        if option and getattr(user, "option", None) != option:
            user.option = option
            fields_to_update.append("option")

        # ✅ AUTO-VALIDATION EC pour un lien epargnecredit
        if is_ec_link:
            if getattr(user, "option", None) != OPTION_EC:
                user.option = OPTION_EC
                if "option" not in fields_to_update:
                    fields_to_update.append("option")
            if not getattr(user, "is_validated", False):
                user.is_validated = True
                fields_to_update.append("is_validated")

        if fields_to_update:
            user.save(update_fields=fields_to_update)

        login(request, user)
        _add_member_to_group(request, user, group)

        if is_ec_link and getattr(user, "is_validated", False):
            messages.success(request, "Bienvenue ! Votre compte est validé pour Épargne & Crédit.")

        return _redirect_by_option(user, group)

    # Cas 2 : un autre compte porte déjà ce nom
    if User.objects.filter(nom__iexact=nom).exclude(phone=phone).exists():
        messages.error(request, "Le nom existe déjà. Choisissez-en un autre.")
        return render(
            request,
            "accounts/inscription_par_invit.html",
            {"group": group, "forced_option": forced_option, "option_labels": OPTION_LABELS},
            status=400,
        )

    # Création du compte
    try:
        alias = _unique_alias_for(nom)
        user = User.objects.create_user(
            nom=nom,
            phone=phone,
            password=password,
            alias=alias,
            option=option,  # forcé selon l'app du groupe
        )

        # ✅ AUTO-VALIDATION EC pour un lien epargnecredit (juste après création)
        if is_ec_link:
            changed = False
            if getattr(user, "option", None) != OPTION_EC:
                user.option = OPTION_EC
                changed = True
            if not getattr(user, "is_validated", False):
                user.is_validated = True
                changed = True
            if changed:
                user.save(update_fields=["option", "is_validated"] if is_ec_link else None)

        messages.success(request, f"Compte créé avec succès pour {nom} (alias : {alias}).")
    except IntegrityError:
        messages.error(request, "Ce nom ou ce numéro est déjà utilisé.")
        return render(
            request,
            "accounts/inscription_par_invit.html",
            {"group": group, "forced_option": forced_option, "option_labels": OPTION_LABELS},
            status=400,
        )
    except Exception as e:
        messages.error(request, f"Erreur lors de la création du compte : {e}")
        return render(
            request,
            "accounts/inscription_par_invit.html",
            {"group": group, "forced_option": forced_option, "option_labels": OPTION_LABELS},
            status=400,
        )

    # Connexion + ajout au groupe
    login(request, user)
    _add_member_to_group(request, user, group)

    if is_ec_link and getattr(user, "is_validated", False):
        messages.success(request, "Bienvenue ! Votre compte est validé pour Épargne & Crédit.")

    return _redirect_by_option(user, group)

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages

def validation_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if request.user.option == "2" and not request.user.is_validated:
            messages.error(request, "⛔ Votre compte doit être validé par l’administrateur avant d’accéder à l’application Épargne & Crédit.")
            return redirect("accounts:attente_validation")
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@validation_required
def dashboard_epargne_credit(request):
    # logique du dashboard
    return render(request, "epargnecredit/dashboard.html")


from django.shortcuts import render

def attente_validation(request):
    return render(request, "accounts/attente_validation.html")
