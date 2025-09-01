# accounts/admin.py
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from .forms import CustomUserCreationFormAdmin, CustomUserChangeFormAdmin

CustomUser = get_user_model()

# Assure-toi qu'il n'est pas déjà enregistré (idempotent)
try:
    admin.site.unregister(CustomUser)
except admin.sites.NotRegistered:
    pass


@admin.register(CustomUser)
class CustomUserAdmin(DjangoUserAdmin):
    """
    Admin unique et propre pour CustomUser.
    Compatible avec le modèle actuel (is_validated seulement).
    """
    add_form = CustomUserCreationFormAdmin
    form = CustomUserChangeFormAdmin
    model = CustomUser

    # Colonnes
    list_display = ("phone", "nom", "option", "is_validated", "is_staff", "is_superuser", "is_active")
    list_filter = ("option", "is_validated", "is_staff", "is_superuser", "is_active")
    search_fields = ("phone", "nom", "alias", "email")
    ordering = ("phone",)
    empty_value_display = "—"

    # Fieldsets pour l'édition
    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        (_("Informations personnelles"), {"fields": ("nom", "alias", "email", "option")}),
        (_("Statut de validation"), {"fields": ("is_validated",)}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Dates importantes"), {"fields": ("last_login", "date_joined")}),
    )

    # Fieldsets pour la création
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("phone", "nom", "alias", "email", "option", "password1", "password2",
                       "is_active", "is_staff", "is_superuser", "is_validated"),
        }),
    )

    # Actions de validation
    actions = ("valider_comptes", "invalider_comptes")

    @admin.action(description="✅ Valider les comptes sélectionnés")
    def valider_comptes(self, request, queryset):
        updated = queryset.update(is_validated=True)
        self.message_user(request, f"{updated} compte(s) validé(s).")

    @admin.action(description="🚫 Invalider les comptes sélectionnés")
    def invalider_comptes(self, request, queryset):
        updated = queryset.update(is_validated=False)
        self.message_user(request, f"{updated} compte(s) invalidé(s).")







