from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from platform_admin.plan_limits import (
    get_plan,
    check_can_add_service,
    check_api_access,
)


class PlanLimitsTests(SimpleTestCase):
    def test_get_plan_defaults(self):
        with patch('platform_admin.plan_limits.Plan') as mock_plan:
            mock_plan.objects.filter.return_value.first.return_value = None
            plan = get_plan('nonexistent-tier')
        self.assertEqual(plan.max_services, 5)
        self.assertEqual(plan.tier, 'nonexistent-tier')

    def test_api_access_denied_on_free(self):
        free = SimpleNamespace(tier='free', name='Free', api_access=False)
        with patch('platform_admin.plan_limits.get_plan_for_business', return_value=free):
            ok, _ = check_api_access(SimpleNamespace(plan='free'))
        self.assertFalse(ok)

    def test_api_access_allowed_on_pro(self):
        pro = SimpleNamespace(tier='pro', name='Pro', api_access=True)
        with patch('platform_admin.plan_limits.get_plan_for_business', return_value=pro):
            ok, _ = check_api_access(SimpleNamespace(plan='pro'))
        self.assertTrue(ok)

    @patch('businesses.models.Service.objects.filter')
    def test_service_limit(self, mock_filter):
        free = SimpleNamespace(
            tier='free', name='Free', max_services=2,
        )
        with patch('platform_admin.plan_limits.get_plan_for_business', return_value=free):
            biz = SimpleNamespace(plan='free', pk='abc')
            mock_filter.return_value.count.return_value = 2
            ok, msg = check_can_add_service(biz)
        self.assertFalse(ok)
        self.assertIn('Free', msg)
