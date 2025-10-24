# candidate_form/permissions.py
from rest_framework import permissions


class IsAdminOrOwnerSubmission(permissions.BasePermission):
    """
    Allow full access for staff/superusers. Regular users can only view/create submissions
    where they are the submitted_by.
    """

    def has_permission(self, request, view):
        # Allow authenticated users (customize as needed)
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # staff or superuser may access any
        if request.user.is_staff or request.user.is_superuser:
            return True
        # owners (submitted_by) can access
        return getattr(obj, "submitted_by_id", None) == request.user.pk
