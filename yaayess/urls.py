from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

from accounts.views import login_view
from accounts.api.auth_views import MobileLoginView

from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
from accounts.jwt_serializer import PhoneTokenObtainPairSerializer


class PhoneTokenObtainPairView(TokenObtainPairView):
    serializer_class = PhoneTokenObtainPairSerializer


urlpatterns = [
    # PAGE PAR DEFAUT → LOGIN
    path('', login_view, name='landing'),
    path('admin/', admin.site.urls),

    path('tontine/', include(('cotisationtontine.urls', 'cotisationtontine'), namespace='cotisationtontine')),
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('epargne/', include(('epargnecredit.urls', 'epargnecredit'), namespace='epargnecredit')),

    # JWT
    path('api/token/', PhoneTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # API mobile
    path("api/mobile/login/", MobileLoginView.as_view(), name="mobile_login"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)