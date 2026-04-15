from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.owner == request.user
    
class IsVerified(BasePermission):
    message = "Please verify your email address to access this resource."
    def has_permission(self, request, view):
        if request.user.is_verified:
            return True
        return False