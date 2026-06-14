from django.utils import timezone

from businesses.models import Business


def global_context(request):
    context = {
        'business': getattr(request, 'business', None),
        'business_slug': getattr(request, 'business_slug', None),
    }

    # Inject active business for authenticated dashboard users
    if request.user.is_authenticated:
        active_id = getattr(request.user, 'active_business_id', None)
        if active_id and not context['business']:
            try:
                context['active_business'] = Business.objects.filter(
                    pk=active_id
                ).first()
            except Exception:
                context['active_business'] = None
        else:
            context['active_business'] = context['business']

        # All businesses this user owns/manages
        try:
            user_biz_ids = request.user.businesses or []
            context['user_businesses'] = Business.objects.filter(
                pk__in=user_biz_ids
            ) if user_biz_ids else Business.objects.none()
        except Exception:
            context['user_businesses'] = []

        # Platform announcements for dashboard users
        try:
            from platform_admin.models import Announcement
            from platform_admin.plan_limits import get_plan_for_user

            now = timezone.now()
            qs = Announcement.objects.filter(status='published')
            user_plan = get_plan_for_user(request.user).tier
            visible = []
            for item in qs:
                if item.expires_at and item.expires_at < now:
                    continue
                if not item.target_all and item.target_plans and user_plan not in item.target_plans:
                    continue
                visible.append(item)
            context['platform_announcements'] = visible[:5]
        except Exception:
            context['platform_announcements'] = []

    return context
