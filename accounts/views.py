from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .forms import CustomUserCreationForm, CustomAuthenticationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth import login
from django.contrib.auth import get_backends

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, get_backends
from django.contrib import messages
from .forms import CustomUserCreationForm

from django.contrib.auth import login
from django.contrib.auth import get_backends


def signup_view(request):
    """
    Crée un compte CustomUser et connecte automatiquement l'utilisateur.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Récupérer le backend compatible
            backend = get_backends()[0]  # prend le premier backend
            login(request, user, backend=f'{backend.__module__}.{backend.__class__.__name__}')

            messages.success(request, f"Bienvenue {user.nom} ! Votre compte a été créé.")
            return redirect('cotisationtontine:dashboard_tontine_simple')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})


def login_view(request):
    """
    Connexion avec nom + mot de passe.
    """
    if request.method == "POST":
        nom = request.POST.get('nom')
        password = request.POST.get('password')
        user = authenticate(request, username=nom, password=password)  # username = nom pour le backend
        if user is not None:
            login(request, user)
            messages.success(request, f"Bienvenue {user.nom} !")
            return redirect('cotisationtontine:dashboard_tontine_simple')
        else:
            messages.error(request, "Nom ou mot de passe incorrect.")
    return render(request, 'accounts/login.html')


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

