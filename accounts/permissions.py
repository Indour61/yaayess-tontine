from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_super_admin


class IsStaffUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff


class IsOptionOne(BasePermission):
    """
    Cotisation & Tontine
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.option == "1"


class IsOptionTwo(BasePermission):
    """
    Épargne & Crédit
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.option == "2"