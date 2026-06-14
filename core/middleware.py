from django.utils.deprecation import MiddlewareMixin
from django.http import Http404


class TenantMiddleware(MiddlewareMixin):
    """
    Identifies the current business tenant from URL path segment or subdomain.
    Attaches `request.business` and `request.business_slug` for downstream use.
    """

    def process_request(self, request):
        request.business = None
        request.business_slug = None

        # Path-based tenancy: /b/<slug>/...
        path = request.path_info
        if path.startswith('/b/'):
            parts = path.split('/')
            if len(parts) >= 3 and parts[2]:
                request.business_slug = parts[2]
                self._attach_business(request, parts[2])
            return

        # Subdomain-based tenancy: <slug>.domain.com
        host = request.get_host().split(':')[0]
        parts = host.split('.')
        if len(parts) >= 3:
            slug = parts[0]
            if slug not in ('www', 'app', 'api', 'admin'):
                request.business_slug = slug
                self._attach_business(request, slug)

    def _attach_business(self, request, slug):
        try:
            from businesses.models import Business
            request.business = Business.objects.filter(slug=slug, is_active=True).first()
        except Exception:
            request.business = None
