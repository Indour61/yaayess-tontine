from django.urls import path, include
from django.contrib import admin
from cotisationtontine.views import landing_view

urlpatterns = [
    path('', landing_view, name='landing'),
    path('admin/', admin.site.urls),

    # Tontine
    path('tontine/', include(('cotisationtontine.urls', 'cotisationtontine'), namespace='cotisationtontine')),

    # Comptes
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),

    # Épargne & Crédit
    path('epargne/', include(('epargnecredit.urls', 'epargnecredit'), namespace='epargnecredit')),
]

