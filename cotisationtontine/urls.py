from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import inscription_par_invit

from .views_api import (
    GroupViewSet, GroupMemberViewSet,
    VersementViewSet, ActionLogViewSet
)

# -----------------------------
# Namespace
# -----------------------------
app_name = 'cotisationtontine'

# -----------------------------
# Router pour l’API REST
# -----------------------------
router = DefaultRouter()
router.register(r'groups', GroupViewSet)
router.register(r'members', GroupMemberViewSet)
router.register(r'versements', VersementViewSet)
router.register(r'logs', ActionLogViewSet)

# -----------------------------
# URL patterns
# -----------------------------
urlpatterns = [
    # --- API ---
    path('api/', include(router.urls)),

    # --- Dashboard ---
    path('dashboard/', views.dashboard_tontine_simple, name='dashboard_tontine_simple'),

    # --- Groupes ---
    path('groups/', views.group_list, name='group_list'),
    path('groups/create/', views.ajouter_groupe_view, name='ajouter_groupe'),
    path('group/<int:group_id>/', views.group_detail, name='group_detail'),

    # --- Membres ---
    path('group/<int:group_id>/membre/ajouter/', views.ajouter_membre_view, name='ajouter_membre'),
    path('group/<int:group_id>/membre/<int:membre_id>/editer/', views.editer_membre_view, name='editer_membre'),
    path('group/<int:group_id>/membre/<int:membre_id>/supprimer/', views.supprimer_membre_view, name='supprimer_membre'),

    # --- Versements ---
    path('versement/initier/<int:member_id>/', views.initier_versement, name='initier_versement'),
    path('versement/callback/', views.versement_callback, name='versement_callback'),
    path('versement/merci/', views.versement_merci, name='versement_merci'),

    # --- Invitations ---
    path('invitation/<uuid:token>/', views.accepter_invitation, name='accepter_invitation'),
    path('group/<int:group_id>/invitation/creer/', views.creer_invitation_view, name='creer_invitation'),

    # --- Tirage ---
    path('group/<int:group_id>/tirage-au-sort/', views.tirage_au_sort_view, name='tirage_au_sort'),
    path('group/<int:group_id>/tirage-resultat/', views.tirage_resultat_view, name='tirage_resultat'),

    # --- Cycle ---
    path('group/<int:group_id>/reset-cycle/', views.reset_cycle_view, name='reset_cycle'),
#    path('group/<int:group_id>/cycle/confirmation-reset/', views.confirm_reset_cycle_view, name='confirm_reset_cycle'),

    path('group/<int:group_id>/lancer-tirage/', views.tirage_au_sort_view, name='lancer_tirage'),

    path('group/<int:group_id>/reset-cycle/', views.reset_cycle_view, name='reset_cycle'),

    path('rejoindre/<uuid:code>/', inscription_par_invit, name='inscription_par_invit')

]

