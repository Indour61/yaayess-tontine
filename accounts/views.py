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


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone
from .models import CustomUser
from epargnecredit.models import Group, GroupMember
from .utils import generate_alias  # ta fonction pour créer un alias unique

@transaction.atomic
def inscription_et_rejoindre(request, code):
    """
    Inscription via un lien d'invitation :
    1️⃣ Vérifie le groupe par code d'invitation
    2️⃣ Crée ou réutilise un compte basé sur le nom et option
    3️⃣ Ajoute l'utilisateur au groupe
    4️⃣ Redirige vers le dashboard approprié selon l'option
    """
    group = get_object_or_404(Group, code_invitation=code)

    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        phone = request.POST.get("phone", "").strip()
        password = request.POST.get("password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()
        option = request.POST.get("option", "").strip()  # Récupère l'option

        if not all([nom, phone, password, confirm_password, option]):
            messages.error(request, "Tous les champs sont requis, y compris le choix de l'option.")
            return render(request, "accounts/inscription_par_invit.html", {"group": group})

        if password != confirm_password:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return render(request, "accounts/inscription_par_invit.html", {"group": group})

        # Chercher si l'utilisateur existe déjà par nom et téléphone
        user = CustomUser.objects.filter(nom=nom).first()

        if user:
            # Authentification si le compte existe
            auth_user = authenticate(request, username=user.phone, password=password)
            if auth_user is None:
                messages.error(request, "Mot de passe incorrect pour ce nom.")
                return render(request, "accounts/inscription_par_invit.html", {"group": group})
            user = auth_user
            messages.info(request, f"Connexion réussie pour {nom}. Vous allez être ajouté au groupe.")
            # Mettre à jour l'option si ce n'est pas défini
            if not user.option:
                user.option = option
                user.save(update_fields=['option'])
        else:
            if CustomUser.objects.filter(phone=phone).exists():
                messages.error(request, "Ce numéro de téléphone est déjà utilisé par un autre utilisateur.")
                return render(request, "accounts/inscription_par_invit.html", {"group": group})

            # Générer un alias unique
            alias_unique = generate_alias(nom)
            while CustomUser.objects.filter(alias=alias_unique).exists():
                alias_unique = generate_alias(nom)

            try:
                user = CustomUser.objects.create_user(
                    nom=nom,
                    phone=phone,
                    password=password,
                    alias=alias_unique,
                    option=option  # sauvegarde de l'option
                )
                messages.success(request, f"Compte créé avec succès pour {nom} (alias: {alias_unique}).")
            except IntegrityError:
                messages.error(request, "Ce nom ou numéro est déjà utilisé.")
                return render(request, "accounts/inscription_par_invit.html", {"group": group})
            except Exception as e:
                messages.error(request, f"Erreur lors de la création du compte: {str(e)}")
                return render(request, "accounts/inscription_par_invit.html", {"group": group})

        # Ajouter au groupe
        try:
            group_member, created_member = GroupMember.objects.get_or_create(
                group=group,
                user=user,
                defaults={'montant': 0, 'date_joined': timezone.now()}
            )
            if created_member:
                messages.success(request, f"Vous avez été ajouté au groupe {group.nom}.")
            else:
                messages.info(request, f"Vous êtes déjà membre du groupe {group.nom}.")
        except Exception as e:
            messages.error(request, f"Erreur lors de l'ajout au groupe: {str(e)}")
            return render(request, "accounts/inscription_par_invit.html", {"group": group})

        # Connexion de l'utilisateur
        login(request, user)
        print(f"📲 Simulé WhatsApp : Bonjour {nom}, vous avez été ajouté au groupe {group.nom}.")

        # Redirection selon l'option
        if user.option == '1':
            return redirect("cotisationtontine:dashboard_tontine_simple")
        else:  # '2'
            return redirect("epargnecredit:dashboard_epargne_credit")

    # GET : affichage du formulaire
    return render(request, "accounts/inscription_par_invit.html", {"group": group})

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

