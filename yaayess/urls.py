from django.urls import path, include
from django.contrib import admin
from cotisationtontine.views import landing_view
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', landing_view, name='landing'),
    path('admin/', admin.site.urls),

    # Tontine
    path('tontine/', include(('cotisationtontine.urls', 'cotisationtontine'), namespace='cotisationtontine')),

    # Comptes
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),

    # Épargne & Crédit
    path('epargne/', include(('epargnecredit.urls', 'epargnecredit'), namespace='epargnecredit')),

    # Assistant IA
    path('ai/', include(('assistant_ai.urls', 'assistant_ai'), namespace='assistant_ai')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
