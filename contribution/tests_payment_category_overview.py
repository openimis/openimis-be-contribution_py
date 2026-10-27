from django.test import TestCase

from contribution.reports.payment_category_overview import payment_category_overview_query
from contribution.test_helpers import create_test_premium
from insuree.models import InsureePolicy
from insuree.test_helpers import create_test_insuree
from location.test_helpers import create_test_village
from policy.test_helpers import create_test_policy2
from product.test_helpers import create_test_product

PAY_DATE = "2031-03-15"


class PaymentCategoryOverviewTest(TestCase):
    """
    The report used to resolve the district as the grand-parent of the family location and to look up
    the number of active members of every policy, so it crashed (KeyError) for a family located above
    village level or for a policy without any active InsureePolicy.
    """

    def setUp(self):
        self.village = create_test_village({"code": "PCOV1"})
        self.ward = self.village.parent
        self.district = self.ward.parent
        self.region = self.district.parent

    def _run(self, product, **kwargs):
        return payment_category_overview_query(None,
                                               date_start=PAY_DATE,
                                               date_end=PAY_DATE,
                                               requested_product_id=product.id,
                                               **kwargs)

    def _create_policy(self, product, chf_id, location):
        insuree = create_test_insuree(custom_props={"chf_id": chf_id},
                                      family_custom_props={"location": location})
        policy, _ = create_test_policy2(product, insuree)
        return policy

    def _assert_family_location_level(self, location, product_code, chf_id):
        product = create_test_product(product_code)
        policy = self._create_policy(product, chf_id, location)
        self.assertEqual(policy.family.location_id, location.id)
        create_test_premium(policy.id, with_payer=False,
                            custom_props={"amount": 1000, "pay_date": PAY_DATE})

        for filters in ({}, {"requested_region_id": self.region.id}, {"requested_district_id": self.district.id}):
            report = self._run(product, **filters)
            self.assertNotIn("error", report, filters)
            self.assertEqual(len(report["data"]), 1, filters)
            line = report["data"][0]
            self.assertEqual(line["district_code"], self.district.code, filters)
            self.assertEqual(line["product_code"], product.code, filters)
            self.assertEqual(report["total_c"], 1000, filters)

    def test_family_located_at_ward_level(self):
        self._assert_family_location_level(self.ward, "PCOW1", "990000101")

    def test_family_located_at_district_level(self):
        self._assert_family_location_level(self.district, "PCOD1", "990000103")

    def test_family_located_at_region_level(self):
        # There is no district above a region: the premium is still reported (without district),
        # it belongs to the requested region but not to any requested district
        product = create_test_product("PCOR1")
        policy = self._create_policy(product, "990000104", self.region)
        create_test_premium(policy.id, with_payer=False,
                            custom_props={"amount": 1000, "pay_date": PAY_DATE})

        for filters in ({}, {"requested_region_id": self.region.id}):
            report = self._run(product, **filters)
            self.assertNotIn("error", report, filters)
            self.assertEqual(len(report["data"]), 1, filters)
            self.assertEqual(report["total_c"], 1000, filters)
        report = self._run(product, requested_district_id=self.district.id)
        self.assertEqual(report["data"], [])
        self.assertEqual(report["total_c"], 0)

    def test_policy_without_active_insuree_policy(self):
        product = create_test_product("PCOW2")
        policy = self._create_policy(product, "990000102", self.village)
        InsureePolicy.objects.filter(policy=policy).update(validity_to=PAY_DATE)
        create_test_premium(policy.id, with_payer=False,
                            custom_props={"amount": 1000, "pay_date": PAY_DATE})
        create_test_premium(policy.id, with_payer=False,
                            custom_props={"amount": -400, "pay_date": PAY_DATE})

        report = self._run(product)
        self.assertNotIn("error", report)
        self.assertEqual(len(report["data"]), 1)
        line = report["data"][0]
        self.assertEqual(line["district_code"], self.district.code)
        self.assertEqual(report["total_c"], 600)
