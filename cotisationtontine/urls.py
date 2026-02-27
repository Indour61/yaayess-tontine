from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views_api import (
    GroupViewSet,
    GroupMemberViewSet,
    VersementViewSet,
    ActionLogViewSet
)

app_name = "cotisationtontine"

# =====================================================
# API REST
# =====================================================

router = DefaultRouter()
router.register(r"groups", GroupViewSet)
router.register(r"members", GroupMemberViewSet)
router.register(r"versements", VersementViewSet)
router.register(r"logs", ActionLogViewSet)

urlpatterns = [

    # ============================
    # API
    # ============================
    path("api/", include(router.urls)),

    # ============================
    # Dashboard
    # ============================
    path("dashboard/", views.dashboard_tontine_simple, name="dashboard_tontine_simple"),

    # ============================
    # Groupes
    # ============================
    path("", views.group_list_view, name="group_list"),
    path("create/", views.ajouter_groupe_view, name="ajouter_groupe"),
    path("<int:group_id>/", views.group_detail, name="group_detail"),

    # ============================
    # Membres
    # ============================
    path("<int:group_id>/membre/ajouter/", views.ajouter_membre_view, name="ajouter_membre"),
    path("<int:group_id>/membre/<int:membre_id>/editer/", views.editer_membre_view, name="editer_membre"),
    path("<int:group_id>/membre/<int:membre_id>/supprimer/", views.supprimer_membre_view, name="supprimer_membre"),

    # ============================
    # Versements (CAISSE INTERNE)
    # ============================
    path("versement/<int:member_id>/initier/", views.initier_versement, name="initier_versement"),
    path("versement/<int:versement_id>/valider/", views.valider_versement, name="valider_versement"),
    path("versement/<int:versement_id>/refuser/", views.refuser_versement, name="refuser_versement"),

    # ============================
    # Tirage
    # ============================
    path("<int:group_id>/tirage/resultat/", views.tirage_resultat_view, name="tirage_resultat"),
    path("<int:group_id>/tirage/", views.tirage_au_sort_view, name="tirage_au_sort"),

    # ============================
    # Cycle
    # ============================
    path("<int:group_id>/reset-cycle/", views.reset_cycle_view, name="reset_cycle"),

    # ============================
    # Historique
    # ============================
    path("<int:group_id>/historique-cycles/", views.historique_cycles_view, name="historique_cycles"),
    path("historique-actions/", views.historique_actions_view, name="historique_actions"),
]
