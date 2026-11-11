"""Premium writes, the policy-delete handler and the reports stay in the user's districts (OP-3322)."""

from datetime import date

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from contribution.gql_mutations import DeletePremiumsMutation, on_policy_mutation, premium_action
from contribution.models import Premium
from contribution.reports.premium_collection import premium_collection_query
from contribution.services import update_or_create_premium
from contribution.test_helpers import create_test_premium
from core.test_helpers import create_right_only_user
from insuree.test_helpers import create_test_insuree
from location.models import Location
from location.test_helpers import create_basic_test_locations
from policy.test_helpers import create_test_policy
from product.test_helpers import create_test_product

PAY_DATE = "2019-01-01"
PAY_DAY = date(2019, 1, 1)


@override_settings(ROW_SECURITY=True)
class PremiumRowScopeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_basic_test_locations()
        cls.product = create_test_product("OP3322C")
        cls.policies = {}
        cls.premiums = {}
        for key, village_code in (("a", "R1D1M1V1"), ("b", "R2D1M1V1")):
            village = Location.objects.get(code=village_code, validity_to__isnull=True)
            insuree = create_test_insuree(
                with_family=True,
                is_head=True,
                custom_props={"current_village": village},
                family_custom_props={"location": village},
            )
            policy = create_test_policy(
                cls.product, insuree, link=True, custom_props={"value": 1000}
            )
            cls.policies[key] = policy
            cls.premiums[key] = create_test_premium(
                policy.id, with_payer=False, custom_props={"receipt": f"OP3322-{key}"}
            )
        cls.premium_user = create_right_only_user(
            "op3322prem",
            [
                "gql_mutation_create_premiums_perms",
                "gql_mutation_update_premiums_perms",
                "gql_mutation_delete_premiums_perms",
            ],
            district_codes=["R1D1"],
        )
        cls.policy_deleter = create_right_only_user(
            "op3322poldel", ["gql_mutation_delete_policies_perms"], district_codes=["R1D1"]
        )
        cls.no_right = create_right_only_user("op3322noright", [], district_codes=["R1D1", "R2D1"])
        cache.clear()

    def setUp(self):
        # Model instances are cached; a rolled-back delete must not be read back.
        cache.clear()

    def _premium(self, key):
        return Premium.objects.get(id=self.premiums[key].id)

    def _policy_delete_signal(self, user, *keys):
        return on_policy_mutation(
            sender=None,
            mutation_class="DeletePoliciesMutation",
            data={"uuids": [self.policies[k].uuid for k in keys]},
            user=user,
        )

    # on_policy_mutation (finding #4)

    def test_policy_delete_handler_only_deletes_premiums_in_scope(self):
        self._policy_delete_signal(self.policy_deleter, "a", "b")

        self.assertIsNotNone(self._premium("a").validity_to)
        self.assertIsNone(self._premium("b").validity_to)

    def test_policy_delete_handler_requires_the_policy_delete_right(self):
        self._policy_delete_signal(self.no_right, "a", "b")
        self._policy_delete_signal(None, "a", "b")

        self.assertIsNone(self._premium("a").validity_to)
        self.assertIsNone(self._premium("b").validity_to)

    # premium mutations and service (finding #6)

    def test_create_on_a_policy_outside_the_scope_is_refused(self):
        data = {
            "policy_uuid": self.policies["b"].uuid,
            "amount": 10,
            "receipt": "OP3322-new",
            "pay_date": PAY_DAY,
            "pay_type": "C",
        }
        with self.assertRaises(Exception):
            premium_action(data, self.premium_user)
        self.assertFalse(Premium.objects.filter(receipt="OP3322-new").exists())

    def test_client_id_cannot_overwrite_a_premium_outside_the_scope(self):
        target = self._premium("b")
        data = {
            "id": target.id,
            "policy_uuid": self.policies["a"].uuid,
            "amount": 1,
            "receipt": "OP3322-hijack",
            "pay_date": PAY_DAY,
            "pay_type": "C",
        }
        premium_action(data, self.premium_user)

        target.refresh_from_db()
        self.assertEqual(target.receipt, "OP3322-b")
        self.assertEqual(target.policy_id, self.policies["b"].id)

    def test_update_by_uuid_outside_the_scope_is_refused(self):
        premium = Premium(
            uuid=self.premiums["b"].uuid,
            policy=self.policies["a"],
            amount=1,
            receipt="OP3322-move",
            pay_date=PAY_DAY,
            pay_type="C",
            audit_user_id=-1,
        )
        with self.assertRaises(ValidationError):
            update_or_create_premium(premium, self.premium_user)
        self.assertEqual(self._premium("b").receipt, "OP3322-b")

    def test_delete_premium_outside_the_scope_is_refused(self):
        DeletePremiumsMutation.async_mutate(
            self.premium_user, uuids=[self.premiums["b"].uuid]
        )

        self.assertIsNone(self._premium("b").validity_to)

    # reports (finding #7)

    def test_premium_collection_report_keeps_own_district(self):
        report = premium_collection_query(
            self.policy_deleter,
            date_start=PAY_DATE,
            date_end=PAY_DATE,
            requested_product_id=self.product.id,
        )

        self.assertEqual({line["district_code"] for line in report["data"]}, {"R1D1"})
