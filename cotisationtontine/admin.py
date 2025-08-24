from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import Group, GroupMember, ActionLog


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('nom', 'admin', 'date_creation', 'montant_base', 'membres_count')
    list_filter = ('date_creation', 'montant_base')
    search_fields = ('nom', 'admin__nom', 'admin__phone')
    ordering = ('-date_creation',)
    readonly_fields = ('code_invitation', 'uuid', 'date_creation')
    fieldsets = (
        ('Informations de base', {
            'fields': ('nom', 'admin', 'montant_base', 'montant_fixe_gagnant')
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_reset'),
            'classes': ('collapse',)
        }),
        ('Codes et tokens', {
            'fields': ('code_invitation', 'invitation_token', 'uuid'),
            'classes': ('collapse',)
        }),
        ('Gagnants', {
            'fields': ('prochain_gagnant',),
            'classes': ('collapse',)
        }),
    )

    def membres_count(self, obj):
        return obj.membres.count()
    membres_count.short_description = 'Nombre de membres'


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'montant', 'actif', 'exit_liste', 'date_ajout', 'date_joined')
    list_filter = ('actif', 'exit_liste', 'date_ajout', 'date_joined', 'group')
    search_fields = ('user__nom', 'user__phone', 'group__nom')
    autocomplete_fields = ('user', 'group')
    readonly_fields = ('date_ajout', 'date_joined')
    list_editable = ('montant', 'actif', 'exit_liste')
    fieldsets = (
        ('Informations de base', {
            'fields': ('user', 'group', 'montant')
        }),
        ('Statut', {
            'fields': ('actif', 'exit_liste')
        }),
        ('Dates', {
            'fields': ('date_ajout', 'date_joined'),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ('user', 'group')
        return self.readonly_fields


@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'date', 'formatted_date')
    list_filter = ('action', 'date', 'user')
    search_fields = ('user__nom', 'user__phone', 'action')
    ordering = ('-date',)
    readonly_fields = ('date',)

    def formatted_date(self, obj):
        return obj.date.strftime('%d/%m/%Y %H:%M')
    formatted_date.short_description = 'Date formatée'
# tontine/admin.py
from django.contrib import admin
from .models import PaiementGagnant


@admin.register(PaiementGagnant)
class PaiementGagnantAdmin(admin.ModelAdmin):
    list_display = ('gagnant_nom', 'groupe_nom', 'montant', 'statut', 'date_paiement')
    list_filter = ('statut', 'group')
    search_fields = ('gagnant__user__nom', 'group__nom', 'transaction_id')
    readonly_fields = ('date_paiement',)

    def gagnant_nom(self, obj):
        return obj.gagnant.user.nom
    gagnant_nom.short_description = "Gagnant"

    def groupe_nom(self, obj):
        return obj.group.nom
    groupe_nom.short_description = "Groupe"
