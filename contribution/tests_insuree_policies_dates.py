"""
On payment the member dates are set by the policy module (OP-3321), with the former
behaviour kept when the policy module has no such service.
"""
import builtins
import datetime
from unittest import mock

from django.test import TestCase

from contribution import services
from insuree.models import InsureePolicy
from insuree.test_helpers import create_test_insuree
from policy.models import Policy
from policy.test_helpers import create_test_policy
from product.test_helpers import create_test_product


class InsureePoliciesDatesTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.product = create_test_product("CTIPDATE")
        cls.insuree = create_test_insuree(with_family=True, custom_props={"chf_id": "CTIPDATE1"})
        cls.policy = create_test_policy(cls.product, cls.insuree, link=True)
        Policy.objects.filter(id=cls.policy.id).update(start_date=datetime.date(2024, 1, 1))
        cls.policy.refresh_from_db()

    def test_policy_service_called(self):
        with mock.patch("policy.services.update_insuree_policies_dates") as service:
            services._update_policy_insurees(self.policy)
            service.assert_called_once_with(self.policy, activation_date=None)
            services._activate_insurees(self.policy, datetime.date(2024, 3, 3))
            service.assert_called_with(self.policy, activation_date=datetime.date(2024, 3, 3))

    def test_fallback_without_the_policy_service(self):
        real_import = builtins.__import__

        def no_service(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "policy.services" and fromlist and "update_insuree_policies_dates" in fromlist:
                raise ImportError("older policy module")
            return real_import(name, globals, locals, fromlist, level)

        Policy.objects.filter(id=self.policy.id).update(expiry_date=datetime.date(2030, 1, 1))
        self.policy.refresh_from_db()
        with mock.patch("builtins.__import__", side_effect=no_service):
            services._update_policy_insurees(self.policy)
            services._activate_insurees(self.policy, datetime.date(2024, 3, 3))
        ip = InsureePolicy.objects.get(policy=self.policy, validity_to__isnull=True)
        self.assertEqual((datetime.date(2030, 1, 1), datetime.date(2024, 3, 3)),
                         (ip.expiry_date, ip.effective_date))

    def test_activation_never_before_the_policy_start(self):
        """a policy dated in the future is not active on the payment already"""
        premium = mock.Mock(pay_date=datetime.date(2023, 11, 11))
        self.assertEqual(datetime.date(2024, 1, 1), services._activation_date(self.policy, premium))
        premium.pay_date = datetime.date(2024, 2, 2)
        self.assertEqual(datetime.date(2024, 2, 2), services._activation_date(self.policy, premium))
