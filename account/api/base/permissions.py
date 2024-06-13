from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS
from utils.base.general import check_raise_exc
from utils.base.logger import err_logger, logger  # noqa


class IsAuthenticatedAdmin(BasePermission):
    def has_permission(self, request, view):
        # Get the user, if the user is staff or admin (open access)
        try:
            if request.user.is_authenticated:
                user = request.user
                if user.staff or user.admin:
                    return True
        except Exception as e:
            err_logger.exception(e)


is_auth_admin = IsAuthenticatedAdmin()
is_auth_normal = IsAuthenticated()


class SuperPerm(BasePermission):
    """
    Permissions to check if user has a project
    staff api key and is authenticated
    Or user is authenticated admin
    """

    def has_permission(self, request, view):
        # Check if the user has project api key
        #if has_staff_key.has_permission(request, view):

        # Check if the user is authenticated
        if is_auth_normal.has_permission(request, view):
            return True

        # Check if the user is an authenticated admin
        if is_auth_admin.has_permission(request, view):
            return True


class CustomerOrReadOnly(BasePermission):
    
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return request.user == obj.user
    

class OwnerCustomPermission(BasePermission):
    
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user