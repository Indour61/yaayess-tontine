from django.contrib import admin
from .models import CustomUser
from .forms import CustomUserCreationFormAdmin, CustomUserChangeFormAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

@admin.register(CustomUser)
class UserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationFormAdmin
    form = CustomUserChangeFormAdmin
    model = CustomUser

    list_display = ('phone', 'nom', 'is_validated', 'is_staff', 'is_super_admin', 'is_active')
    list_filter = ('is_validated', 'is_staff', 'is_super_admin', 'is_active')
    search_fields = ('phone', 'nom')
    ordering = ('phone',)

    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Informations personnelles', {'fields': ('nom',)}),
        ('Statut de validation', {'fields': ('is_validated',)}),  # ✅
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_super_admin', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'nom', 'password1', 'password2', 'is_active', 'is_staff', 'is_super_admin', 'is_validated'),
        }),
    )

    # ✅ Actions admin pour valider / invalider en masse
    actions = ('valider_comptes', 'invalider_comptes')

    @admin.action(description="✅ Valider les comptes sélectionnés")
    def valider_comptes(self, request, queryset):
        updated = queryset.update(is_validated=True)
        self.message_user(request, f"{updated} compte(s) validé(s).")

    @admin.action(description="🚫 Invalider les comptes sélectionnés")
    def invalider_comptes(self, request, queryset):
        updated = queryset.update(is_validated=False)
        self.message_user(request, f"{updated} compte(s) invalidé(s).")

