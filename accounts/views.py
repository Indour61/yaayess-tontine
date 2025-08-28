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


def _resolve_group_by_code(code: str) -> Group:
    """
    Récupère un Group à partir d'un code d'invitation.
    - Essaie d'abord par code_invitation (ou invitation_code / uuid si présent)
    - Fallback : si code numérique, essaie par id
    """
    # Essais par champs courants (tous ne sont pas forcément présents)
    candidate_q = Q()
    for field in ("code_invitation", "invitation_code", "uuid", "code"):
        try:
            # Si le champ existe, on l'utilise
            Group._meta.get_field(field)  # peut lever FieldDoesNotExist
            candidate_q |= Q(**{field: code})
        except Exception:
            pass

    if candidate_q:
        try:
            return Group.objects.get(candidate_q)
        except Group.DoesNotExist:
            pass
        except Group.MultipleObjectsReturned:
            # Si collision improbable, on prend le plus récent
            return Group.objects.filter(candidate_q).order_by("-id").first()

    # Fallback par id numérique
    if code.isdigit():
        return get_object_or_404(Group, id=int(code))

    # Rien trouvé
    return get_object_or_404(Group, id=-1)  # forcera un 404


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
@transaction.atomic
def inscription_et_rejoindre(request: HttpRequest, code: str) -> HttpResponse:
    """
    1) Retrouve le groupe depuis <code> (champ code_invitation de préférence)
    2) Si l'utilisateur existe (phone), authentifie puis ajoute au groupe
    3) Sinon crée le compte (nom, phone, password, option) puis ajoute au groupe
    4) Redirige vers le bon dashboard selon user.option

    Affiche explicitement "nom existe déjà" si un autre compte porte déjà ce nom.
    """
    group = _resolve_group_by_code(code)

    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        phone = request.POST.get("phone", "").strip()
        password = request.POST.get("password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()
        option = request.POST.get("option", "").strip()  # "1" (tontine) ou "2" (épargne/crédit)

        # --------------- validations rapides ---------------
        if not all([nom, phone, password, confirm_password, option]):
            messages.error(request, "Tous les champs sont requis, y compris le choix de l'option.")
            return render(request, "accounts/inscription_par_invit.html", {"group": group})

        if password != confirm_password:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return render(request, "accounts/inscription_par_invit.html", {"group": group})

        # --------------- cas 1 : un compte existe déjà avec ce phone ---------------
        existing_by_phone = User.objects.filter(phone=phone).first()
        if existing_by_phone:
            user = authenticate(request, username=phone, password=password)
            if user is None:
                messages.error(request, "Mot de passe incorrect pour ce numéro de téléphone.")
                return render(request, "accounts/inscription_par_invit.html", {"group": group})

            # Mise à jour facultative du nom si vide
            if not user.nom:
                user.nom = nom

            # Si option non définie, on prend celle choisie
            if not getattr(user, "option", None):
                user.option = option
            user.save(update_fields=["nom", "option"])  # no-op si inchangé

            login(request, user)
            _add_member_to_group(user, group)
            return _redirect_by_option(user)

        # --------------- cas 2 : un autre compte porte déjà ce nom ---------------
        existing_by_name = User.objects.filter(nom__iexact=nom).exclude(phone=phone).exists()
        if existing_by_name:
            messages.error(request, "Le nom existe déjà. Choisissez-en un autre.")
            return render(request, "accounts/inscription_par_invit.html", {"group": group})

        # --------------- création du compte ---------------
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

        # --------------- connexion + ajout au groupe ---------------
        login(request, user)
        _add_member_to_group(user, group)
        return _redirect_by_option(user)

    # GET : afficher le formulaire avec infos de groupe (montant_base, nom, etc.)
    return render(request, "accounts/inscription_par_invit.html", {"group": group})


def _add_member_to_group(user: User, group: Group) -> None:
    """Ajoute l'utilisateur au groupe si pas déjà membre, avec messages adaptés."""
    try:
        member, created = GroupMember.objects.get_or_create(
            group=group,
            user=user,
            defaults={"montant": 0, "date_joined": timezone.now()},
        )
        if created:
            messages.success(
                request=None,  # sera ignoré par Django messages si None, on force ci-dessous
                message=f"Vous avez été ajouté au groupe {getattr(group, 'nom', group.id)}.",
            )
        else:
            messages.info(
                request=None,
                message=f"Vous êtes déjà membre du groupe {getattr(group, 'nom', group.id)}.",
            )
    except TypeError:
        # Fallback safe : utiliser l'API messages seulement si un request est en cours
        pass
    except Exception as e:
        # On peut logguer e si besoin
        messages.error(request=None, message=f"Erreur lors de l'ajout au groupe : {e}")


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

