from django.contrib import admin
from cotisationtontine.views import landing_view
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.views import TokenObtainPairView
from accounts.jwt_serializer import PhoneTokenObtainPairSerializer

class PhoneTokenObtainPairView(TokenObtainPairView):
    serializer_class = PhoneTokenObtainPairSerializer


urlpatterns = [
    path('', landing_view, name='landing'),
    path('admin/', admin.site.urls),

    path('tontine/', include(('cotisationtontine.urls', 'cotisationtontine'), namespace='cotisationtontine')),
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('epargne/', include(('epargnecredit.urls', 'epargnecredit'), namespace='epargnecredit')),

    # JWT personnalisé
    path('api/token/', PhoneTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)