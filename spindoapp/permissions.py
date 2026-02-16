from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

# Permission Error Messages
PERMISSION_DENIED = "Permission denied"
ONLY_ADMIN_MESSAGE = "Only admin can access this resource."
ONLY_STAFF_MESSAGE = "Only staff can access this resource."
ONLY_ADMIN_OR_STAFF_MESSAGE = "Only admin or staff can access this resource."
ONLY_ADMIN_CAN_CREATE_STAFF = "Only admin can create staff"
ONLY_CUSTOMERS_CAN_UPDATE = "Only customers can update their own details"
ONLY_ADMIN_AND_STAFF_CAN_UPDATE = "Only admin and staff can update staff details"
ONLY_ACCESS_OWN_DATA = "You can only access your own data"
ONLY_UPDATE_OWN_DATA = "You can only update your own data"
MOBILE_NUMBER_CANNOT_CHANGE = "Mobile number cannot be changed"
CANNOT_CHANGE_ACTIVE_STATUS = "You cannot change active status"
CUSTOMER_NOT_FOUND = "Customer not found"
STAFF_NOT_FOUND = "Staff not found"
UNIQUE_ID_REQUIRED = "unique_id is required"
UNIQUE_ID_REQUIRED_FOR_CUSTOMER = "unique_id is required for customer access"
UNIQUE_ID_REQUIRED_FOR_STAFF = "unique_id is required for staff access"
EMAIL_ALREADY_REGISTERED = "Email already registered"
MOBILE_NUMBER_ALREADY_REGISTERED = "Mobile number already registered"


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
        return request.user.role in ["admin", "staff", "staffadmin"]


class IsStaffAdminOwner(BasePermission):
    """
    Permission class to check if staffadmin can only access their own data.
    """
    message = "You can only access your own staff data."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Admin can access all staff data
        if request.user.role == "admin":
            return True
        # Staff admin can only access if unique_id is provided in query params
        if request.user.role == "staffadmin":
            unique_id = request.query_params.get('unique_id')
            return unique_id is not None and unique_id == request.user.unique_id
        return False


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
    return user and user.is_authenticated and user.role in ["admin", "staff", "staffadmin"]
