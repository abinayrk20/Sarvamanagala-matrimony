from rest_framework import permissions

class IsAdminOrStaff(permissions.BasePermission):
    """
    Allows access only to authenticated admin or staff users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsActiveAndPaidMember(permissions.BasePermission):
    """
    Ensures user is logged in, their account is active, and their ₹2,000 GPay registration has been verified.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_staff:
            return True
        if not request.user.is_active:
            return False
        # Check registration payment status
        if hasattr(request.user, 'registration_payment'):
            return request.user.registration_payment.status == 'PAID'
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to allow only owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'profile'):
            return obj.profile.user == request.user
        return False
