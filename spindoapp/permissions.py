from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied


class IsAdmin(BasePermission):
    """
    Permission class to check if user is admin.
    """
    message = "Only admin can access this resource."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role == "admin"


class IsStaff(BasePermission):
    """
    Permission class to check if user is staff.
    """
    message = "Only staff can access this resource."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role == "staff"


class IsAdminOrStaff(BasePermission):
    """
    Permission class to check if user is admin or staff.
    """
    message = "Only admin or staff can access this resource."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ["admin", "staff"]


def check_admin_role(user):
    """
    Utility function to check if user has admin role.
    Returns True if user is admin, False otherwise.
    """
    return user and user.is_authenticated and user.role == "admin"


def check_staff_role(user):
    """
    Utility function to check if user has staff role.
    Returns True if user is staff, False otherwise.
    """
    return user and user.is_authenticated and user.role == "staff"


def check_admin_or_staff_role(user):
    """
    Utility function to check if user has admin or staff role.
    Returns True if user is admin or staff, False otherwise.
    """
    return user and user.is_authenticated and user.role in ["admin", "staff"]
