from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import Group, GroupMember, ActionLog

from django.contrib import admin
from django.db.models import Sum
from .models import Group

def _has_field(model, name: str) -> bool:
    return any(getattr(f, "name", None) == name for f in model._meta.get_fields())

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    # Colonnes sûres uniquement (les méthodes gèrent les None/absences)
    list_display = ("nom", "admin_nom", "admin_phone", "date_creation", "montant_base", "membres_count_safe")
    list_filter = ("date_creation",)  # évite pour l'instant "montant_base" si ce champ varie
    search_fields = ("nom", "admin__nom", "admin__alias", "admin__phone")
    ordering = ("-date_creation",)

    # ----- champs en lecture seule dynamiques -----
    def get_readonly_fields(self, request, obj=None):
        ro = ["date_creation"]  # sûr
        for fld in ("code_invitation", "uuid"):
            if _has_field(Group, fld):
                ro.append(fld)
        return tuple(ro)

    # ----- fieldsets dynamiques (n’inclut que les champs existants) -----
    def get_fieldsets(self, request, obj=None):
        base_fields = ["nom", "admin"]
        if _has_field(Group, "montant_base"):
            base_fields.append("montant_base")
        if _has_field(Group, "montant_fixe_gagnant"):
            base_fields.append("montant_fixe_gagnant")

        dates_fields = ["date_creation"]
        if _has_field(Group, "date_reset"):
            dates_fields.append("date_reset")

        codes_fields = []
        if _has_field(Group, "code_invitation"):
            codes_fields.append("code_invitation")
        if _has_field(Group, "invitation_token"):
            codes_fields.append("invitation_token")
        if _has_field(Group, "uuid"):
            codes_fields.append("uuid")

        gagnants_fields = []
        if _has_field(Group, "prochain_gagnant"):
            gagnants_fields.append("prochain_gagnant")

        fieldsets = [
            ("Informations de base", {"fields": tuple(base_fields)}),
            ("Dates", {"fields": tuple(dates_fields), "classes": ("collapse",)}),
        ]
        if codes_fields:
            fieldsets.append(("Codes et tokens", {"fields": tuple(codes_fields), "classes": ("collapse",)}))
        if gagnants_fields:
            fieldsets.append(("Gagnants", {"fields": tuple(gagnants_fields), "classes": ("collapse",)}))

        return fieldsets

    # ----- affichages sécurisés -----
    def admin_nom(self, obj):
        return getattr(getattr(obj, "admin", None), "nom", "—")
    admin_nom.short_description = "Admin (Nom)"

    def admin_phone(self, obj):
        return getattr(getattr(obj, "admin", None), "phone", "—")
    admin_phone.short_description = "Admin (Téléphone)"

    def membres_count_safe(self, obj):
        # essaie différentes relations possibles : membres_ec, membres, members
        for rel_name in ("membres_ec", "membres", "members"):
            rel = getattr(obj, rel_name, None)
            if rel is not None:
                try:
                    return rel.count()
                except Exception:
                    pass
        return 0
    membres_count_safe.short_description = "Nombre de membres"


from django.contrib import admin
from django.db.models import Sum, F
from .models import GroupMember, ActionLog

# ---------- Admin GroupMember ----------

@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    """
    Admin robuste + perf :
    - select_related pour éviter N+1
    - colonnes sûres (méthodes tolérantes aux None)
    - actions rapides (activer/désactiver, sortie de liste, reset montant)
    """
    list_display = (
        "user_nom", "user_alias", "user_phone",
        "group", "montant",
        "actif", "exit_liste",
        "date_ajout", "date_joined",
    )
    list_filter = ("actif", "exit_liste", "group", "date_ajout", "date_joined")
    search_fields = ("user__nom", "user__alias", "user__phone", "group__nom")
    autocomplete_fields = ("user", "group")
    readonly_fields = ("date_ajout", "date_joined")
    # ⚠️ Les champs list_editable ne doivent pas inclure le premier champ cliquable
    list_editable = ("montant", "actif", "exit_liste")
    date_hierarchy = "date_ajout"
    list_per_page = 50
    empty_value_display = "—"

    fieldsets = (
        ("Informations de base", {
            "fields": ("user", "group", "montant"),
        }),
        ("Statut", {
            "fields": ("actif", "exit_liste"),
        }),
        ("Dates", {
            "fields": ("date_ajout", "date_joined"),
            "classes": ("collapse",),
        }),
    )

    # Perf : éviter N+1
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("user", "group")

    # Méthodes d'affichage sûres
    def user_nom(self, obj):
        return getattr(getattr(obj, "user", None), "nom", "—")
    user_nom.short_description = "Nom"
    user_nom.admin_order_field = "user__nom"

    def user_alias(self, obj):
        return getattr(getattr(obj, "user", None), "alias", "—")
    user_alias.short_description = "Alias"
    user_alias.admin_order_field = "user__alias"

    def user_phone(self, obj):
        return getattr(getattr(obj, "user", None), "phone", "—")
    user_phone.short_description = "Téléphone"
    user_phone.admin_order_field = "user__phone"

    # Actions rapides
    actions = (
        "activer_membres",
        "desactiver_membres",
        "marquer_sortie",
        "annuler_sortie",
        "reset_montant",
    )

    @admin.action(description="✅ Activer les membres sélectionnés")
    def activer_membres(self, request, queryset):
        updated = queryset.update(actif=True)
        self.message_user(request, f"{updated} membre(s) activé(s).")

    @admin.action(description="🚫 Désactiver les membres sélectionnés")
    def desactiver_membres(self, request, queryset):
        updated = queryset.update(actif=False)
        self.message_user(request, f"{updated} membre(s) désactivé(s).")

    @admin.action(description="📤 Marquer 'sortie de liste'")
    def marquer_sortie(self, request, queryset):
        updated = queryset.update(exit_liste=True)
        self.message_user(request, f"{updated} membre(s) marqué(s) sortis de liste.")

    @admin.action(description="↩️ Annuler 'sortie de liste'")
    def annuler_sortie(self, request, queryset):
        updated = queryset.update(exit_liste=False)
        self.message_user(request, f"{updated} membre(s) réintégré(s) dans la liste.")

    @admin.action(description="🧹 Remettre le montant à 0")
    def reset_montant(self, request, queryset):
        updated = queryset.update(montant=0)
        self.message_user(request, f"Montant remis à zéro pour {updated} membre(s).")


# ---------- Admin ActionLog ----------

@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    """
    Admin ActionLog :
    - colonnes lisibles (user nom/phone, date formatée)
    - tri et filtres utiles
    - perf via select_related
    """
    list_display = ("user_safe", "user_phone", "action", "date", "formatted_date")
    list_filter = ("action", "date", "user")
    search_fields = ("user__nom", "user__phone", "action")
    ordering = ("-date",)
    readonly_fields = ("date",)
    date_hierarchy = "date"
    list_per_page = 50
    empty_value_display = "—"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("user")

    def user_safe(self, obj):
        u = getattr(obj, "user", None)
        return getattr(u, "nom", str(u)) if u else "—"
    user_safe.short_description = "Utilisateur"
    user_safe.admin_order_field = "user__nom"

    def user_phone(self, obj):
        return getattr(getattr(obj, "user", None), "phone", "—")
    user_phone.short_description = "Téléphone"
    user_phone.admin_order_field = "user__phone"

    def formatted_date(self, obj):
        try:
            return obj.date.strftime("%d/%m/%Y %H:%M")
        except Exception:
            return "—"
    formatted_date.short_description = "Date formatée"
    formatted_date.admin_order_field = "date"
