from rest_framework.permissions import BasePermission, IsAuthenticated


class IsBusinessOwner(BasePermission):
    """Allow access only to owners/managers of the business."""

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        biz_ids = [str(b) for b in (user.businesses or [])]
        from businesses.models import Business
        if hasattr(obj, 'business'):
            return str(obj.business_id) in biz_ids
        if isinstance(obj, Business):
            return str(obj.pk) in biz_ids
        return False


class IsBusinessMember(BasePermission):
    """Allow access to any member (owner, manager, staff) of the business."""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
