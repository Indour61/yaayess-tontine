from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views_api import GroupViewSet, GroupMemberViewSet, VersementViewSet, ActionLogViewSet

app_name = 'epargnecredit'

# --- Router API REST ---
router = DefaultRouter()
router.register(r'groups', GroupViewSet)
router.register(r'members', GroupMemberViewSet)
router.register(r'versements', VersementViewSet)
router.register(r'logs', ActionLogViewSet)

urlpatterns = [

    # ================= API =================
    path('api/', include(router.urls)),

    # ================= Dashboard =================
    path('dashboard/', views.dashboard_epargne_credit, name='dashboard_epargne_credit'),

    # ================= Groupes =================
    path('', views.group_list_view, name='group_list'),
    path('create/', views.ajouter_groupe_view, name='ajouter_groupe'),
    path('<int:group_id>/', views.group_detail, name='group_detail'),

    # ================= Membres =================
    path('<int:group_id>/membre/ajouter/', views.ajouter_membre_view, name='ajouter_membre'),

    # ================= Versements CAISSE =================
    path(
        'versement/initier/<int:member_id>/',
        views.initier_versement,
        name='initier_versement'
    ),

    path(
        'versement/valider/<int:versement_id>/',
        views.valider_versement,
        name='valider_versement'
    ),

    path(
        'versement/refuser/<int:versement_id>/',
        views.refuser_versement,
        name='refuser_versement'
    ),

    # ================= Cycle =================
    path('<int:group_id>/reset-cycle/', views.reset_cycle_view, name='reset_cycle'),

    # ================= Historique =================
    path('<int:group_id>/historique-cycles/', views.historique_cycles_view, name='historique_cycles'),
    path("historique-actions/", views.historique_actions_view, name="historique_actions"),

    # ================= Prêts =================
    path("pret/nouveau/<int:member_id>/", views.demande_pret, name="demande_pret"),
    path("pret/<int:pk>/valider/", views.pret_valider, name="pret_valider"),
    path("pret/<int:pk>/refuser/", views.pret_refuser, name="pret_refuser"),
    path("pret/<int:pk>/remboursement/", views.pret_remboursement_detail, name="pret_remboursement_detail"),

    # ================= Groupe remboursement =================
    path(
        "remboursement/<int:group_id>/",
        views.group_detail_remboursement,
        name="group_detail_remboursement"
    ),

    # ================= Partage fin de cycle =================
    path(
        "epargne/<int:group_id>/partager-fin-de-cycle/",
        views.share_cycle_view,
        name="share_cycle"
    ),
]