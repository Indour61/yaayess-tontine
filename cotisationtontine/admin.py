from django.contrib import admin
from .models import Group, GroupMember, Invitation, ActionLog


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


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ('phone', 'group', 'expire_at', 'used')
    list_filter = ('used',)
    search_fields = ('phone', 'group__nom')

"""
@admin.register
class VersementAdmin(admin.ModelAdmin):
    list_display = ('member', 'montant', 'methode', 'date')  # 'statut' supprimé
    list_filter = ('methode',)  # 'statut' supprimé
    search_fields = ('member__user__nom', 'member__group__nom', 'transaction_id')
    autocomplete_fields = ('member',)
"""

@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'date')
    list_filter = ('user',)
    search_fields = ('user__nom', 'action')
    ordering = ('-date',)
