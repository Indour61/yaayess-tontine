from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import CustomUser
from .forms import CustomUserCreationFormAdmin, CustomUserChangeFormAdmin


@admin.register(CustomUser)
class CustomUserAdmin(DjangoUserAdmin):
    """
    Admin pour CustomUser avec affichage de l'acceptation des Conditions d’utilisation.
    """
    add_form = CustomUserCreationFormAdmin
    form = CustomUserChangeFormAdmin
    model = CustomUser

    # Colonnes
    list_display = (
        "phone", "nom", "option",
        "is_validated",
        "terms_version", "terms_accepted_at",
        "is_staff", "is_superuser", "is_active",
    )
    list_filter = (
        "option", "is_validated",
        "terms_version",
        "is_staff", "is_superuser", "is_active",
    )
    search_fields = ("phone", "nom", "alias", "email")
    ordering = ("phone",)
    empty_value_display = "—"

    # Champs en lecture seule (⚠️ pas de date_joined car non présent sur AbstractBaseUser)
    readonly_fields = (
        "terms_accepted_at", "terms_version",
        "validated_at", "validated_by",
        "last_login",
    )

    # Fieldsets pour l'édition
    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        (_("Informations personnelles"), {
            "fields": ("nom", "alias", "email", "option"),
        }),
        (_("Statut de validation"), {
            "fields": ("is_validated", "validated_at", "validated_by"),
        }),
        (_("Conditions d’utilisation"), {
            "description": _("Historique d’acceptation enregistré automatiquement lors de l’inscription."),
            "fields": ("terms_version", "terms_accepted_at"),
        }),
        (_("Permissions"), {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
        }),
        (_("Dates importantes"), {
            "fields": ("last_login",),  # ✅ on ne met plus date_joined
        }),
    )

    # Fieldsets pour la création
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "phone", "nom", "alias", "email", "option",
                "password1", "password2",
                "is_active", "is_staff", "is_superuser", "is_validated",
            ),
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
