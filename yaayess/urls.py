from django.contrib import admin
from cotisationtontine.views import landing_view
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

from django.urls import path, include


urlpatterns = [
    path('', landing_view, name='landing'),
    path('admin/', admin.site.urls),

 #   path("accounts/", include("allauth.urls")),  # <= ajoute allauth
 #   path("post-login/", post_login_router, name="post_login_router"),

    # Tontine
    path('tontine/', include(('cotisationtontine.urls', 'cotisationtontine'), namespace='cotisationtontine')),

    # Comptes
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),

    # Épargne & Crédit
    path('epargne/', include(('epargnecredit.urls', 'epargnecredit'), namespace='epargnecredit')),

    # Assistant IA
    path('ai/', include(('assistant_ai.urls', 'assistant_ai'), namespace='assistant_ai')),


    path("legal/", include(("assistant_ai.legal_urls", "legal"), namespace="legal")),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

