from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import liste_paiements_gagnants
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
    path('', views.group_list_view, name='group_list'),                  # /groups/
    path('create/', views.ajouter_groupe_view, name='ajouter_groupe'),   # /groups/create/
    path('<int:group_id>/', views.group_detail, name='group_detail'),    # /groups/<id>/

    # --- Membres ---
    path('<int:group_id>/membre/ajouter/', views.ajouter_membre_view, name='ajouter_membre'),
    path('<int:group_id>/membre/<int:membre_id>/editer/', views.editer_membre_view, name='editer_membre'),
    path('<int:group_id>/membre/<int:membre_id>/supprimer/', views.supprimer_membre_view, name='supprimer_membre'),

    # --- Versements ---
    path('versement/initier/<int:member_id>/', views.initier_versement, name='initier_versement'),
    path('versement/callback/', views.versement_callback, name='versement_callback'),
    path('versement/merci/', views.versement_merci, name='versement_merci'),

    # --- Invitations ---
    path('invitation/<uuid:token>/', views.accepter_invitation, name='accepter_invitation'),
    path('<int:group_id>/invitation/creer/', views.creer_invitation_view, name='creer_invitation'),

    # --- Tirage ---
    path('<int:group_id>/tirage-au-sort/', views.tirage_au_sort_view, name='tirage_au_sort'),
    path('<int:group_id>/tirage-resultat/', views.tirage_resultat_view, name='tirage_resultat'),

    # --- Cycle ---
    path('<int:group_id>/reset-cycle/', views.reset_cycle_view, name='reset_cycle'),
    path('<int:group_id>/lancer-tirage/', views.tirage_au_sort_view, name='lancer_tirage'),

    # --- Rejoindre groupe ---
    path('rejoindre/<uuid:code>/', views.inscription_et_rejoindre, name='inscription_et_rejoindre'),

    # --- Paiement gagnant ---
    path('<int:group_id>/payer-gagnant/', views.payer_gagnant, name='payer_gagnant'),
    path('paiements-gagnants/', liste_paiements_gagnants, name='paiements_gagnants'),
    path('paiement_gagnant/callback/', views.paiement_gagnant_callback, name='paiement_gagnant_callback'),
    path('paiement_gagnant/merci/', views.paiement_gagnant_merci, name='paiement_gagnant_merci'),

    # --- Historique cycles & actions ---
    path('<int:group_id>/historique-cycles/', views.historique_cycles_view, name='historique_cycles'),
    path("historique-actions/", views.historique_actions_view, name="historique_actions"),
]

