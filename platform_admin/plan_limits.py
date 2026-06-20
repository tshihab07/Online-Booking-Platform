"""Plan tier limits and usage tracking for Bookify SaaS."""

from django.utils import timezone

from platform_admin.models import Plan, UserUsage


DEFAULT_FREE_LIMITS = {
    'max_businesses': 1,
    'max_services': 5,
    'max_staff': 3,
    'max_bookings_per_month': 50,
    'max_calendar_views': 100,
    'custom_themes': False,
    'analytics_enabled': True,
    'api_access': False,
}


def get_plan(tier='free'):
    """Return Plan row for tier, or a lightweight stand-in with defaults."""
    if not tier:
        tier = 'free'
    plan = Plan.objects.filter(tier=tier, is_active=True).first()
    if plan:
        return plan

    class _PlanDefaults:
        def __init__(self, tier_name):
            self.tier = tier_name
            self.name = tier_name.title()
            self.is_active = True
            for key, value in DEFAULT_FREE_LIMITS.items():
                setattr(self, key, value)

    return _PlanDefaults(tier)


def get_plan_for_business(business):
    return get_plan(getattr(business, 'plan', None) or 'free')


def get_plan_for_user(user):
    from businesses.models import Business

    active_id = getattr(user, 'active_business_id', None)
    if active_id:
        biz = Business.objects.filter(pk=active_id).first()
        if biz:
            return get_plan_for_business(biz)
    biz_ids = user.businesses or []
    if biz_ids:
        biz = Business.objects.filter(pk__in=biz_ids).first()
        if biz:
            return get_plan_for_business(biz)
    return get_plan('free')


def _usage_for_business(business):
    from accounts.models import CustomUser

    owner = CustomUser.objects.filter(businesses__overlap=[str(business.pk)]).first()
    if owner:
        usage, _ = UserUsage.objects.get_or_create(user=owner)
        _maybe_reset_monthly(usage)
        return usage, owner
    return None, None


def _maybe_reset_monthly(usage):
    today = timezone.localdate()
    if usage.last_reset.month != today.month or usage.last_reset.year != today.year:
        usage.reset_monthly()


def bookings_this_month_for_business(business):
    from bookings.models import Booking

    today = timezone.localdate()
    month_start = today.replace(day=1)
    return Booking.objects.filter(business=business, date__gte=month_start).count()


def check_can_add_business(user):
    plan = get_plan_for_user(user)
    current = len(user.businesses or [])
    if current >= plan.max_businesses:
        return False, (
            f'Your {plan.name} plan allows up to {plan.max_businesses} business(es). '
            'Upgrade your plan in billing settings or contact support.'
        )
    return True, ''


def check_can_add_service(business):
    from businesses.models import Service

    plan = get_plan_for_business(business)
    current = Service.objects.filter(business=business).count()
    if current >= plan.max_services:
        return False, (
            f'Your {plan.name} plan allows up to {plan.max_services} services. '
            'Upgrade to add more.'
        )
    return True, ''


def check_can_add_staff(business):
    from businesses.models import Staff

    plan = get_plan_for_business(business)
    current = Staff.objects.filter(business=business).count()
    if current >= plan.max_staff:
        return False, (
            f'Your {plan.name} plan allows up to {plan.max_staff} staff members. '
            'Upgrade to add more.'
        )
    return True, ''


def check_can_create_booking(business):
    plan = get_plan_for_business(business)
    count = bookings_this_month_for_business(business)
    if count >= plan.max_bookings_per_month:
        return False, (
            f'This business has reached its monthly booking limit ({plan.max_bookings_per_month}) '
            f'on the {plan.name} plan.'
        )
    return True, ''


def check_api_access(business):
    plan = get_plan_for_business(business)
    if not plan.api_access:
        return False, f'API access requires a plan with API enabled (current: {plan.name}).'
    return True, ''


def check_analytics_enabled(business):
    plan = get_plan_for_business(business)
    if not plan.analytics_enabled:
        return False, f'Analytics is not included on the {plan.name} plan.'
    return True, ''


def check_custom_themes(business):
    plan = get_plan_for_business(business)
    if not plan.custom_themes:
        return False, f'Custom themes require an upgraded plan (current: {plan.name}).'
    return True, ''


def record_booking_created(business):
    usage, _ = _usage_for_business(business)
    if usage:
        usage.bookings_this_month += 1
        usage.total_bookings += 1
        usage.save(update_fields=['bookings_this_month', 'total_bookings', 'updated_at'])


def record_api_call(business):
    usage, _ = _usage_for_business(business)
    if usage:
        usage.api_calls_this_month += 1
        usage.save(update_fields=['api_calls_this_month', 'updated_at'])
