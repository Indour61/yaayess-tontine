from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser
from .forms import CustomUserCreationFormAdmin, CustomUserChangeFormAdmin

from django.contrib import admin
from .models import CustomUser
from .forms import CustomUserCreationFormAdmin, CustomUserChangeFormAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class UserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationFormAdmin
    form = CustomUserChangeFormAdmin
    model = CustomUser

    list_display = ('phone', 'nom', 'is_staff', 'is_super_admin', 'is_active')
    list_filter = ('is_staff', 'is_super_admin', 'is_active')
    search_fields = ('phone', 'nom')
    ordering = ('phone',)

    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Informations personnelles', {'fields': ('nom',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_super_admin', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'nom', 'password1', 'password2', 'is_active', 'is_staff', 'is_super_admin'),
        }),
    )

# ✅ Enregistrement unique avec protection
try:
    admin.site.register(CustomUser, UserAdmin)
except admin.sites.AlreadyRegistered:
    pass
