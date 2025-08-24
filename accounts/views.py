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


def signup_view(request):
    """
    Crée un compte CustomUser et ajoute automatiquement l'utilisateur à un groupe
    si 'group_id' est présent dans GET (invitation) ou POST (formulaire admin).
    """
    # Vérifier si l'utilisateur est déjà connecté
    if request.user.is_authenticated:
        messages.info(request, "Vous êtes déjà connecté.")
        return redirect('cotisationtontine:dashboard_tontine_simple')

    # Récupérer group_id depuis GET ou POST
    group_id = request.GET.get('group_id') or request.POST.get('group_id')
    group = None
    if group_id:
        try:
            group = get_object_or_404(Group, id=group_id)
        except (ValueError, Group.DoesNotExist):
            messages.error(request, "Le groupe spécifié n'existe pas.")
            group = None

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()

                # Connexion automatique
                login(request, user)

                # Ajout automatique au groupe si group_id fourni
                if group:
                    try:
                        GroupMember.objects.get_or_create(
                            group=group,
                            user=user,
                            defaults={'date_joined': timezone.now()}
                        )
                        messages.success(request, f"Vous avez été ajouté au groupe {group.nom}.")
                    except IntegrityError:
                        messages.info(request, f"Vous êtes déjà membre du groupe {group.nom}.")

                messages.success(request, f"Bienvenue {user.nom} ! Votre compte a été créé.")

                # Redirection selon la présence du groupe
                if group:
                    return redirect('cotisationtontine:group_detail', group_id=group.id)
                else:
                    return redirect('cotisationtontine:dashboard_tontine_simple')

            except Exception as e:
                messages.error(request, f"Une erreur s'est produite lors de la création du compte: {str(e)}")
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/signup.html', {
        'form': form,
        'group': group,
    })


def login_view(request):
    """
    Connexion des utilisateurs via nom et mot de passe.
    Redirection vers group_detail du groupe auquel il appartient.
    """
    # Vérifier si l'utilisateur est déjà connecté
    if request.user.is_authenticated:
        messages.info(request, "Vous êtes déjà connecté.")
        # Rediriger vers le tableau de bord ou le groupe approprié
        group_member = GroupMember.objects.filter(user=request.user).first()
        if group_member:
            return redirect(reverse("cotisationtontine:group_detail", args=[group_member.group.id]))
        else:
            return redirect("cotisationtontine:dashboard_tontine_simple")

    if request.method == "POST":
        # Utiliser le formulaire d'authentification personnalisé
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            nom = form.cleaned_data.get('username')  # Le champ s'appelle username mais contient le nom
            password = form.cleaned_data.get('password')

            # Authentifier avec le nom
            user = authenticate(request, username=nom, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f"Connexion réussie. Bienvenue {user.nom} !")

                # Redirection vers le premier groupe du membre
                group_member = GroupMember.objects.filter(user=user).first()
                if group_member:
                    return redirect(reverse("cotisationtontine:group_detail", args=[group_member.group.id]))
                else:
                    return redirect("cotisationtontine:dashboard_tontine_simple")
            else:
                messages.error(request, "Nom ou mot de passe incorrect.")
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = CustomAuthenticationForm()

    return render(request, "accounts/login.html", {'form': form})


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
from django.core.exceptions import ValidationError

# Assurez-vous d'importer CustomUser
from .models import CustomUser
from cotisationtontine.models import Group, GroupMember


def inscription_et_rejoindre(request, code):
    """
    Inscription via un lien d'invitation :
    1️⃣ Vérifie le groupe par code d'invitation
    2️⃣ Crée ou réutilise un compte basé sur le nom
    3️⃣ Ajoute l'utilisateur au groupe
    4️⃣ Redirige vers la page détail du groupe
    """
    # Vérifier que le groupe existe
    group = get_object_or_404(Group, code_invitation=code)

    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        phone = request.POST.get("phone", "").strip()
        password = request.POST.get("password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        # ✅ Vérification des champs obligatoires
        if not nom or not phone or not password or not confirm_password:
            messages.error(request, "Tous les champs sont requis.")
            return render(request, "accounts/inscription_par_invit.html", {"group": group})

        if password != confirm_password:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return render(request, "accounts/inscription_par_invit.html", {"group": group})

        # ✅ Vérifier si un utilisateur avec ce nom existe déjà
        user = None
        try:
            user = CustomUser.objects.get(nom=nom)
        except CustomUser.DoesNotExist:
            pass  # L'utilisateur n'existe pas, nous le créerons plus tard

        if user:
            # Authentifier l'utilisateur existant
            auth_user = authenticate(request, username=nom, password=password)
            if auth_user is None:
                messages.error(request, "Mot de passe incorrect pour ce nom.")
                return render(request, "accounts/inscription_par_invit.html", {"group": group})

            messages.info(request, f"Connexion réussie pour {nom}. Vous allez être ajouté au groupe.")
            user = auth_user
        else:
            # Vérifier si le téléphone est déjà utilisé
            if CustomUser.objects.filter(phone=phone).exists():
                messages.error(request, "Ce numéro de téléphone est déjà utilisé par un autre utilisateur.")
                return render(request, "accounts/inscription_par_invit.html", {"group": group})

            # Création d'un nouvel utilisateur
            try:
                user = CustomUser.objects.create_user(
                    nom=nom,
                    phone=phone,
                    password=password
                )
                messages.success(request, f"Compte créé avec succès pour {nom}.")
            except IntegrityError:
                messages.error(request, "Ce nom est déjà utilisé par un autre utilisateur.")
                return render(request, "accounts/inscription_par_invit.html", {"group": group})
            except Exception as e:
                messages.error(request, f"Erreur lors de la création du compte: {str(e)}")
                return render(request, "accounts/inscription_par_invit.html", {"group": group})

        # ✅ Ajout de l'utilisateur au groupe (si pas déjà membre)
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

        # ✅ Connecter l'utilisateur
        login(request, user)

        # ✅ Simulation d'envoi WhatsApp
        print(f"📲 Simulé WhatsApp : Bonjour {nom}, vous avez été ajouté au groupe {group.nom}.")

        # ✅ Redirection vers la page du groupe
        return redirect(reverse("cotisationtontine:group_detail", args=[group.id]))

    # Si méthode GET → Afficher le formulaire
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


"""
from django.contrib.auth.models import BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('Le numéro de téléphone est obligatoire')
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone, password, **extra_fields)
"""