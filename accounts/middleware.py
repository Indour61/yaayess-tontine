from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone


class RoleRequiredMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        path = request.path

        # Pages publiques autorisées
        public_paths = [
            '/accounts/login',
            '/accounts/signup',
            '/accounts/logout',
            '/admin',
            '/static',
            '/media',
            '/abonnement-requis'
        ]

        # Autoriser les chemins publics
        if any(path.startswith(p) for p in public_paths):
            return self.get_response(request)

        # Vérification connexion utilisateur
        if not request.user.is_authenticated:
            messages.error(request, "Veuillez vous connecter.")
            return redirect('accounts:login')

        # Vérification abonnement (paiement manuel)
        if not request.user.is_superuser:

            if hasattr(request.user, "abonnement_actif"):

                # Vérifier expiration abonnement
                if request.user.date_expiration:
                    if request.user.date_expiration < timezone.now():
                        request.user.abonnement_actif = False
                        request.user.save()

                # Bloquer si abonnement inactif
                if not request.user.abonnement_actif:
                    messages.warning(
                        request,
                        "Votre abonnement YaayESS n'est pas actif."
                    )
                    return redirect('abonnement_requis')

        return self.get_response(request)