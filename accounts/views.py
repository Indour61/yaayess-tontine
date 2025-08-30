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


@login_required
def profile_view(request):
    """
    Affiche et permet de modifier le profil de l'utilisateur.
    """
    if request.method == 'POST':
        # Logique de mise à jour du profil
        nom = request.POST.get('nom')
        email = request.POST.get('email')
        phone = request.POST.get('phone')

        if nom and nom != request.user.nom:
            # Vérifier si le nom n'est pas déjà utilisé
            if CustomUser.objects.filter(nom=nom).exclude(id=request.user.id).exists():
                messages.error(request, "Ce nom est déjà utilisé par un autre utilisateur.")
            else:
                request.user.nom = nom
                messages.success(request, "Votre nom a été mis à jour.")

        if email:
            request.user.email = email
            messages.success(request, "Votre email a été mis à jour.")

        if phone and phone != request.user.phone:
            # Vérifier si le téléphone n'est pas déjà utilisé
            if CustomUser.objects.filter(phone=phone).exclude(id=request.user.id).exists():
                messages.error(request, "Ce numéro de téléphone est déjà utilisé par un autre utilisateur.")
            else:
                request.user.phone = phone
                messages.success(request, "Votre numéro de téléphone a été mis à jour.")

        request.user.save()
        return redirect('accounts:profile')

    return render(request, 'accounts/profile.html')


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.db import IntegrityError
import random
import string

from .models import CustomUser
from cotisationtontine.models import Group, GroupMember


def generate_alias(nom):
    """
    Génère un alias unique basé sur le nom + un suffixe aléatoire.
    Exemple: Fatou Diop → fatou.diop.8372
    """
    base_alias = nom.lower().replace(" ", ".")
    suffix = "".join(random.choices(string.digits, k=4))
    return f"{base_alias}.{suffix}"


#from __future__ import annotations

# ======================================================
# accounts/views.py — version simplifiée & robuste
# Objectif : faciliter l'ajout d'un membre via un lien
# Route attendue : /accounts/rejoindre/<code>/
#   (name='inscription_et_rejoindre' dans accounts/urls.py)
#
# Hypothèses :
# - AUTH_USER_MODEL utilise le téléphone comme identifiant (USERNAME_FIELD='phone').
# - Le modèle Group (cotisationtontine) possède idéalement un champ "code_invitation".
#   En fallback, on sait aussi rejoindre par id numérique.
# - GroupMember a une contrainte d'unicité (group, user).
# ======================================================

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




def _redirect_by_option(user: User) -> HttpResponse:
    """Redirige selon l'option choisie par l'utilisateur."""
    if getattr(user, "option", None) == "1":
        member = GroupMember.objects.filter(user=user).order_by("-id").first()
        if member:
            try:
                return redirect(reverse("cotisationtontine:group_detail", args=[member.group.id]))
            except Exception:
                pass
        return redirect("cotisationtontine:dashboard_tontine_simple")
    # Option "2" (ou autre) => épargne/crédit
    return redirect("epargnecredit:dashboard_epargne_credit")


# ----------------------------------------------------
# Inscription via lien d'invitation
# ----------------------------------------------------
# accounts/views.py
from typing import Optional
from django.apps import apps
from django.contrib import messages
from django.contrib.auth import authenticate, login, get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie

User = get_user_model()

# ---------- Helpers ----------

def _get_field_names(Model) -> set:
    return {f.name for f in Model._meta.get_fields()}

def _find_group_in_model(Model, code: str):
    """
    Cherche un Group dans Model en testant plusieurs champs possibles.
    Utilise filter().first() pour éviter les erreurs MultipleObjectsReturned.
    """
    fields = _get_field_names(Model)
    q = Q()
    for field in ("code_invitation", "invitation_code", "uuid", "code", "slug"):
        if field in fields:
            q |= Q(**{field: code})

    if q:
        obj = Model.objects.filter(q).order_by("-id").first()
        if obj:
            return obj

    if code.isdigit() and "id" in fields:
        return Model.objects.filter(id=int(code)).first()

    return None

def _resolve_group_by_code(code: str):
    """
    Recherche un Group par code dans:
      - cotisationtontine.Group
      - epargnecredit.Group
    Puis via les modèles Invitation (accounts/cotisationtontine/epargnecredit) s'ils existent.
    Lève une 404 si rien n'est trouvé.
    """
    code = (code or "").strip()
    # 1) Directement dans les deux modèles Group
    for app_label in ("cotisationtontine", "epargnecredit"):
        try:
            Model = apps.get_model(app_label, "Group")
        except LookupError:
            Model = None
        if not Model:
            continue
        g = _find_group_in_model(Model, code)
        if g:
            return g

    # 2) Via Invitation -> group
    for app_label in ("accounts", "cotisationtontine", "epargnecredit"):
        try:
            Invitation = apps.get_model(app_label, "Invitation")
        except LookupError:
            Invitation = None
        if not Invitation:
            continue

        inv = (
            Invitation.objects.select_related("group")
            .filter(Q(code=code) | Q(token=code) | Q(uuid=code))
            .order_by("-id")
            .first()
        )
        if inv and getattr(inv, "group", None):
            return inv.group

    # 3) Pas trouvé
    raise Http404("Invitation ou groupe introuvable.")

def _redirect_by_option(user: User) -> HttpResponse:
    """
    Redirige vers le bon dashboard selon user.option:
      - "1" => Tontine
      - "2" => Épargne/Crédit
    """
    opt = str(getattr(user, "option", "")).strip()
    if opt == "1":
        return redirect("cotisationtontine:dashboard_tontine_simple")
    if opt == "2":
        return redirect("epargnecredit:dashboard_epargne_credit")
    # fallback si option inconnue
    messages.info(None, "Option non reconnue, redirection vers l’accueil.")
    return redirect("landing")  # adapte au nom de ta vue d’accueil

def _unique_alias_for(nom: str) -> str:
    """
    Génère un alias unique à partir du nom.
    """
    base = (nom or "user").strip().lower().replace(" ", "_")
    alias = base
    i = 1
    while User.objects.filter(alias=alias).exists():
        i += 1
        alias = f"{base}_{i}"
    return alias

def _add_member_to_group(request, user: User, group) -> None:
    """
    Ajoute l'utilisateur au group correspondant (Tontine/Epargne).
    """
    from cotisationtontine.models import GroupMember as TontineMember
    from epargnecredit.models import GroupMember as EpargneMember

    app_label = group._meta.app_label
    MemberModel = TontineMember if app_label == "cotisationtontine" else (
        EpargneMember if app_label == "epargnecredit" else None
    )

    if MemberModel is None:
        messages.error(request, "Type de groupe inconnu.")
        return

    member, created = MemberModel.objects.get_or_create(
        group=group,
        user=user,
        defaults={"montant": 0, "date_joined": timezone.now()},
    )
    if created:
        messages.success(
            request,
            f"✅ Vous avez été ajouté au groupe « {getattr(group, 'nom', group.id)} »."
        )
    else:
        messages.info(
            request,
            f"ℹ️ Vous êtes déjà membre du groupe « {getattr(group, 'nom', group.id)} »."
        )

# ---------- Vue principale ----------

@ensure_csrf_cookie
@csrf_protect
@transaction.atomic
def inscription_et_rejoindre(request: HttpRequest, code: str) -> HttpResponse:
    """
    1) Retrouve le groupe depuis <code>
    2) Si l'utilisateur existe (phone), authentifie puis ajoute au groupe
    3) Sinon crée le compte (nom, phone, password, option), puis ajoute au groupe
    4) Redirige vers le bon dashboard selon user.option
    Affiche explicitement "nom existe déjà" si un autre compte porte déjà ce nom.
    """
    try:
        group = _resolve_group_by_code(code)
    except Http404:
        messages.error(request, "Lien d’invitation invalide ou expiré.")
        return render(request, "accounts/inscription_par_invit.html", {"group": None}, status=404)

    if request.method == "GET":
        # Affiche le formulaire avec les infos du groupe
        return render(request, "accounts/inscription_par_invit.html", {"group": group})

    # ----------- POST -----------
    nom = request.POST.get("nom", "").strip()
    phone = request.POST.get("phone", "").strip()
    password = request.POST.get("password", "").strip()
    confirm_password = request.POST.get("confirm_password", "").strip()
    option = request.POST.get("option", "").strip()  # "1" (tontine) ou "2" (épargne/crédit)

    # Validations rapides
    if not all([nom, phone, password, confirm_password, option]):
        messages.error(request, "Tous les champs sont requis, y compris le choix de l'option.")
        return render(request, "accounts/inscription_par_invit.html", {"group": group})

    if password != confirm_password:
        messages.error(request, "Les mots de passe ne correspondent pas.")
        return render(request, "accounts/inscription_par_invit.html", {"group": group})

    # Cas 1 : un compte existe déjà avec ce phone
    existing_by_phone = User.objects.filter(phone=phone).first()
    if existing_by_phone:
        # NOTE: si USERNAME_FIELD='phone', on peut passer username=phone
        user = authenticate(request, username=phone, password=password)
        if user is None:
            messages.error(request, "Mot de passe incorrect pour ce numéro de téléphone.")
            return render(request, "accounts/inscription_par_invit.html", {"group": group})

        # Mise à jour facultative du nom si vide
        if not user.nom:
            user.nom = nom

        # Renseigner option si absente
        if not getattr(user, "option", None):
            user.option = option

        user.save(update_fields=["nom", "option"])
        login(request, user)
        _add_member_to_group(request, user, group)
        return _redirect_by_option(user)

    # Cas 2 : un autre compte porte déjà ce nom
    if User.objects.filter(nom__iexact=nom).exclude(phone=phone).exists():
        messages.error(request, "Le nom existe déjà. Choisissez-en un autre.")
        return render(request, "accounts/inscription_par_invit.html", {"group": group})

    # Création du compte
    try:
        alias = _unique_alias_for(nom)
        user = User.objects.create_user(
            nom=nom,
            phone=phone,
            password=password,
            alias=alias,
            option=option,
        )
        messages.success(request, f"Compte créé avec succès pour {nom} (alias : {alias}).")
    except IntegrityError:
        messages.error(request, "Ce nom ou ce numéro est déjà utilisé.")
        return render(request, "accounts/inscription_par_invit.html", {"group": group})
    except Exception as e:
        messages.error(request, f"Erreur lors de la création du compte : {e}")
        return render(request, "accounts/inscription_par_invit.html", {"group": group})

    # Connexion + ajout au groupe
    login(request, user)
    _add_member_to_group(request, user, group)
    return _redirect_by_option(user)


# ----------------------------------------------------
# Auth classique (signup / login / logout / profil)
# ----------------------------------------------------
@transaction.atomic
def signup_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        messages.info(request, "Vous êtes déjà connecté.")
        return _redirect_by_option(request.user)

    group_id = request.GET.get("group_id") or request.POST.get("group_id")
    group = get_object_or_404(Group, id=group_id) if group_id else None

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)

                if group:
                    _add_member_to_group(user, group)

                messages.success(request, f"Bienvenue {user.nom} ! Votre compte a été créé.")
                return _redirect_by_option(user)
            except Exception as e:
                messages.error(request, f"Erreur lors de la création du compte : {e}")
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = CustomUserCreationForm()

    return render(request, "accounts/signup.html", {"form": form, "group": group})


def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        messages.info(request, "Vous êtes déjà connecté.")
        return _redirect_by_option(request.user)

    if request.method == "POST":
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Connexion réussie. Bienvenue {user.nom} !")
            return _redirect_by_option(user)
        else:
            messages.error(request, "Numéro/nom ou mot de passe incorrect, ou option invalide.")
    else:
        form = CustomAuthenticationForm()

    return render(request, "accounts/login.html", {"form": form})


@login_required
def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect("accounts:login")


@login_required
def profile_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        nom = request.POST.get("nom")
        email = request.POST.get("email")
        phone = request.POST.get("phone")

        if nom and nom != request.user.nom:
            if User.objects.filter(nom=nom).exclude(id=request.user.id).exists():
                messages.error(request, "Ce nom est déjà utilisé par un autre utilisateur.")
            else:
                request.user.nom = nom
                messages.success(request, "Votre nom a été mis à jour.")

        if email:
            request.user.email = email
            messages.success(request, "Votre email a été mis à jour.")

        if phone and phone != request.user.phone:
            if User.objects.filter(phone=phone).exclude(id=request.user.id).exists():
                messages.error(request, "Ce numéro de téléphone est déjà utilisé par un autre utilisateur.")
            else:
                request.user.phone = phone
                messages.success(request, "Votre numéro de téléphone a été mis à jour.")

        request.user.save()
        return redirect("accounts:profile")

    return render(request, "accounts/profile.html")

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

