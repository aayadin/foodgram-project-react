from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS


class RegistrationOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        else:
            return not request.user or not request.user.is_authenticated
