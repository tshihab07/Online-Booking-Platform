from django.shortcuts import render
from businesses.models import Business


def home(request):
    """Main SaaS marketing landing page."""
    featured = Business.objects.filter(is_active=True, plan__in=['pro', 'enterprise'])[:6]
    return render(request, 'core/home.html', {'featured_businesses': featured})


def handler404(request, exception):
    return render(request, 'core/404.html', {
        'request_path': request.path,
    }, status=404)
