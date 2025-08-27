from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import liste_paiements_gagnants
from .views_api import GroupViewSet, GroupMemberViewSet, VersementViewSet, ActionLogViewSet

app_name = 'epargnecredit'

# --- Router API REST ---
router = DefaultRouter()
router.register(r'groups', GroupViewSet)
router.register(r'members', GroupMemberViewSet)
router.register(r'versements', VersementViewSet)
router.register(r'logs', ActionLogViewSet)

urlpatterns = [
    # --- API ---
    path('api/', include(router.urls)),

    # --- Dashboard ---
    path('dashboard/', views.dashboard_epargne_credit, name='dashboard_epargne_credit'),

    # --- Groupes ---
    path('', views.group_list_view, name='group_list'),
    path('create/', views.ajouter_groupe_view, name='ajouter_groupe'),
    path('<int:group_id>/', views.group_detail, name='group_detail'),

    # --- Membres ---
    path('<int:group_id>/membre/ajouter/', views.ajouter_membre_view, name='ajouter_membre'),
    path('<int:group_id>/membre/<int:membre_id>/editer/', views.editer_membre_view, name='editer_membre'),
    path('<int:group_id>/membre/<int:membre_id>/supprimer/', views.supprimer_membre_view, name='supprimer_membre'),

    # --- Versements ---
    path('versement/initier/<int:member_id>/', views.initier_versement, name='initier_versement'),
    path('versement/callback/', views.versement_callback, name='versement_callback'),
    path('versement/merci/', views.versement_merci, name='versement_merci'),

    # --- Invitations ---
#    path('<int:group_id>/inviter/', views.inviter_membre_view, name='inviter_membre'),

    # --- Tirage ---
    path('<int:group_id>/tirage-au-sort/', views.tirage_au_sort_view, name='tirage_au_sort'),
    path('<int:group_id>/tirage-resultat/', views.tirage_resultat_view, name='tirage_resultat'),
    path('<int:group_id>/lancer-tirage/', views.tirage_au_sort_view, name='lancer_tirage'),

    # --- Cycle ---
    path('<int:group_id>/reset-cycle/', views.reset_cycle_view, name='reset_cycle'),

    # --- Paiement gagnant ---
    path('<int:group_id>/payer-gagnant/', views.payer_gagnant, name='payer_gagnant'),
    path('paiements-gagnants/', liste_paiements_gagnants, name='paiements_gagnants'),
    path('paiement_gagnant/callback/', views.paiement_gagnant_callback, name='paiement_gagnant_callback'),
    path('paiement_gagnant/merci/', views.paiement_gagnant_merci, name='paiement_gagnant_merci'),

    # --- Historique cycles & actions ---
    path('<int:group_id>/historique-cycles/', views.historique_cycles_view, name='historique_cycles'),
    path("historique-actions/", views.historique_actions_view, name="historique_actions"),
]
