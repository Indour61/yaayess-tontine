from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required



from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import login, get_backends
from django.contrib import messages
from .forms import CustomUserCreationForm
from cotisationtontine.models import Group, GroupMember


def signup_view(request):
    """
    Crée un compte CustomUser et ajoute automatiquement l'utilisateur à un groupe
    si 'group_id' est présent dans GET (invitation) ou POST (formulaire admin).
    """
    # Récupérer group_id depuis GET ou POST
    group_id = request.GET.get('group_id') or request.POST.get('group_id')
    group = None
    if group_id:
        group = get_object_or_404(Group, id=group_id)

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Connexion automatique
            backend = get_backends()[0]
            login(request, user, backend=f'{backend.__module__}.{backend.__class__.__name__}')

            # Ajout automatique au groupe si group_id fourni
            if group:
                GroupMember.objects.get_or_create(group=group, user=user)

            messages.success(request, f"Bienvenue {user.nom} ! Votre compte a été créé.")

            # Redirection selon la présence du groupe
            if group:
                return redirect('cotisationtontine:group_detail', group_id=group.id)
            else:
                return redirect('cotisationtontine:dashboard_tontine_simple')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/signup.html', {
        'form': form,
        'group': group,  # Permet de passer group_id dans le template pour un champ caché si besoin
    })

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from cotisationtontine.models import GroupMember

def login_view(request):
    """
    Connexion des utilisateurs via nom et mot de passe.
    Redirection vers group_detail du groupe auquel il appartient.
    """
    if request.method == "POST":
        nom_input = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        if not nom_input or not password:
            messages.error(request, "Nom et mot de passe requis.")
            return render(request, "accounts/login.html")

        user = authenticate(request, username=nom_input, password=password)
        if user:
            # ⚠️ Important : définir backend pour login si nécessaire
            if not hasattr(user, 'backend'):
                user.backend = 'accounts.backend.NomBackend'

            login(request, user)

            # Redirection vers le premier groupe du membre
            group_member = GroupMember.objects.filter(user=user).first()
            if group_member:
                return redirect(reverse("cotisationtontine:group_detail", args=[group_member.group.id]))
            else:
                messages.info(request, "Vous n'êtes membre d'aucun groupe pour l'instant.")
                return redirect("accounts:login")
        else:
            messages.error(request, "Nom ou mot de passe incorrect.")
            return render(request, "accounts/login.html")

    return render(request, "accounts/login.html")


# ✅ Vue de déconnexion
def logout_view(request):
    """
    Déconnecte l'utilisateur et redirige vers la page de connexion.
    """
    logout(request)
    messages.success(request, "Vous avez été déconnecté.")
    return redirect('accounts:login')


# ✅ Optionnel : restreindre l'accès à certaines pages
@login_required
def profile_view(request):
    """
    Exemple de vue protégée (non obligatoire).
    """
    return render(request, 'accounts/profile.html', {
        'user': request.user
    })


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

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from accounts.models import CustomUser
from cotisationtontine.models import Group, GroupMember
from accounts.backends import NomBackend


def inscription_et_rejoindre(request, code):
    """
    Inscription via un lien d'invitation :
    1️⃣ Vérifie le groupe par code d'invitation
    2️⃣ Crée ou réutilise un compte basé sur le nom
    3️⃣ Authentifie via NomBackend
    4️⃣ Ajoute l'utilisateur au groupe
    5️⃣ Redirige vers la page détail du groupe
    """
    # Vérifier que le groupe existe
    group = get_object_or_404(Group, code_invitation=code)

    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        phone = request.POST.get("phone", "").strip()
        password = request.POST.get("password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        # ✅ Vérification des champs
        if not nom or not phone or not password or not confirm_password:
            messages.error(request, "Tous les champs sont requis.")
            return render(request, "accounts/inscription_par_invit.html", {"group": group})

        if password != confirm_password:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return render(request, "accounts/inscription_par_invit.html", {"group": group})

        # ✅ Vérifier si un utilisateur avec ce nom existe
        user = CustomUser.objects.filter(nom=nom).first()

        if not user:
            # Création du nouvel utilisateur
            user = CustomUser.objects.create(
                phone=phone,
                nom=nom,
                password=make_password(password)  # hashage du mot de passe
            )
            messages.success(request, f"Compte créé avec succès pour {nom}.")
        else:
            messages.info(request, f"Un compte existe déjà pour le nom {nom}. Tentative de connexion...")


        # ✅ Ajout au groupe
        group_member, created_member = GroupMember.objects.get_or_create(
            group=group,
            user=user,
            defaults={'montant': 0}
        )

        if created_member:
            messages.success(request, f"Vous avez été ajouté au groupe {group.nom}.")
        else:
            messages.info(request, f"Vous êtes déjà membre du groupe {group.nom}.")

        # ✅ Simulation d'envoi WhatsApp
        print(f"📲 Simulé WhatsApp : Bonjour {nom}, vous avez été ajouté au groupe {group.nom}.")

        # ✅ Redirection vers la page du groupe
        return redirect(reverse("cotisationtontine:group_detail", args=[group.id]))

    # Si méthode GET → Afficher le formulaire
    return render(request, "accounts/inscription_par_invit.html", {"group": group})


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