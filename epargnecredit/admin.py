from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import Group, GroupMember, ActionLog


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('nom', 'admin_nom', 'admin_phone', 'date_creation', 'montant_base', 'membres_count')
    list_filter = ('date_creation', 'montant_base')
    search_fields = ('nom', 'admin__nom', 'admin__alias', 'admin__phone')
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

    # Affichage personnalisé pour admin
    def admin_nom(self, obj):
        return obj.admin.nom
    admin_nom.short_description = 'Admin (Nom)'

    def admin_phone(self, obj):
        return obj.admin.phone
    admin_phone.short_description = 'Admin (Téléphone)'

    # Compteur des membres
    def membres_count(self, obj):
        return obj.membres.count()
    membres_count.short_description = 'Nombre de membres'

@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ('user_nom', 'user_alias', 'user_phone', 'group', 'montant', 'actif', 'exit_liste', 'date_ajout', 'date_joined')
    list_filter = ('actif', 'exit_liste', 'date_ajout', 'date_joined', 'group')
    search_fields = ('user__nom', 'user__alias', 'user__phone', 'group__nom')
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



    # Champs personnalisés
    def user_nom(self, obj):
        return obj.user.nom
    user_nom.short_description = 'Nom'

    def user_alias(self, obj):
        return getattr(obj.user, 'alias', '-')  # Affiche '-' si alias n'existe pas
    user_alias.short_description = 'Alias'

    def user_phone(self, obj):
        return obj.user.phone
    user_phone.short_description = 'Téléphone'


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

