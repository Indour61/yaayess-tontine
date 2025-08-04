from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from django.urls import path

from .views_api import (
    GroupViewSet, GroupMemberViewSet,
    VersementViewSet, ActionLogViewSet
)

# -----------------------------
# Router pour l’API REST
# -----------------------------
router = DefaultRouter()
router.register(r'groups', GroupViewSet)
router.register(r'members', GroupMemberViewSet)
router.register(r'versements', VersementViewSet)
router.register(r'logs', ActionLogViewSet)

# -----------------------------
# Namespace
# -----------------------------
app_name = 'cotisationtontine'

# -----------------------------
# URL patterns
# -----------------------------
urlpatterns = [
    # --- API ---
    path('api/', include(router.urls)),

    # --- Dashboard principal ---
    path('dashboard/', views.dashboard_tontine_simple, name='dashboard_tontine_simple'),

    # --- Gestion des groupes ---
    path('groups/', views.group_list, name='group_list'),
    path('groups/create/', views.ajouter_groupe_view, name='ajouter_groupe'),
    path('group/<int:group_id>/', views.group_detail, name='group_detail'),  # ✅ Détail du groupe



    # --- Gestion des membres ---
    path('group/<int:group_id>/membre/ajouter/', views.ajouter_membre_view, name='ajouter_membre'),
    path('group/<int:group_id>/membre/<int:membre_id>/editer/', views.editer_membre_view, name='editer_membre'),
    path('group/<int:group_id>/membre/<int:membre_id>/supprimer/', views.supprimer_membre_view, name='supprimer_membre'),

    # --- Versements ---
#    path('group/<int:group_id>/versement/ajouter/', views.ajouter_versement_view, name='ajouter_versement'),
    path('versement/initier/<int:member_id>/', views.initier_versement, name='initier_versement'),
    path('versement/callback/', views.versement_callback, name='versement_callback'),
    path('versement/merci/', views.versement_merci, name='versement_merci'),

    # --- Cycle ---
#    path('group/<int:group_id>/reset-cycle/', views.reset_cycle_view, name='reset_cycle'),

    path('invitation/<uuid:token>/', views.accepter_invitation, name='accepter_invitation'),
    path('group/<int:group_id>/invitation/creer/', views.creer_invitation_view, name='creer_invitation'),

    path('group/<int:group_id>/tirage-au-sort/', views.tirage_au_sort_view, name='tirage_au_sort'),

    path('group/<int:group_id>/reset-cycle/', views.reset_cycle_view, name='reset_cycle'),
    path('group/<int:group_id>/reset-cycle/confirm/', views.confirm_reset_cycle_view, name='confirm_reset_cycle'),

    path('group/<int:group_id>/tirage-resultat/', views.tirage_resultat_view, name='tirage_resultat'),

]
