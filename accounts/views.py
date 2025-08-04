from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .forms import CustomUserCreationForm, CustomAuthenticationForm


# ✅ Vue d'inscription
def signup_view(request):
    """
    Permet de créer un compte CustomUser.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Bienvenue {user.nom or user.phone} ! Votre compte a été créé.")
            # Redirige vers le dashboard épargne-crédit par défaut
            return redirect('cotisationtontine:dashboard_tontine_simple')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})


# ✅ Vue de connexion
def login_view(request):
    """
    Permet de se connecter avec phone + mot de passe.
    """
    if request.method == 'POST':
        form = CustomAuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Bienvenue {user.nom or user.phone} !")
            return redirect('cotisationtontine:dashboard_tontine_simple')
        else:
            messages.error(request, "Numéro ou mot de passe incorrect.")
    else:
        form = CustomAuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


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

