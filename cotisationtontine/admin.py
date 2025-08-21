from django.contrib import admin
from .models import Group, GroupMember, ActionLog


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('nom', 'date_creation')
    search_fields = ('nom',)
    ordering = ('-date_creation',)


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'actif', 'date_ajout')
    list_filter = ('actif',)
    search_fields = ('user__nom', 'user__phone', 'group__nom')
    autocomplete_fields = ('user', 'group')



@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'date')
    list_filter = ('user',)
    search_fields = ('user__nom', 'action')
    ordering = ('-date',)

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
