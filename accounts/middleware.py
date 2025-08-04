from django.shortcuts import redirect
from django.contrib import messages

class RoleRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Laisse passer les pages publiques
        if path.startswith('/accounts/login') or path.startswith('/accounts/signup') or path.startswith('/static'):
            return self.get_response(request)

        # Vérifie que l'utilisateur est connecté pour les pages dashboard
        if path.startswith('/dashboard/') and not request.user.is_authenticated:
            messages.error(request, "Veuillez vous connecter.")
            return redirect('accounts:login')

        # Ici tu peux mettre d'autres restrictions si besoin pour admin
        # ex : if path.startswith('/admin-dashboard/') and not request.user.is_superuser:

        return self.get_response(request)


