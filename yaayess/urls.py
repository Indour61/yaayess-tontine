from django.contrib import admin
from django.urls import path, include
from cotisationtontine.views import landing_view


urlpatterns = [
#    path('', landing_view, name='landing'),
    path('', landing_view, name='landing'),

    path('admin/', admin.site.urls),

    path('', include(('cotisationtontine.urls', 'cotisationtontine'), namespace='cotisationtontine')),
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),

]
