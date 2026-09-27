import uuid

from contribution.test_helpers import create_test_premium
from core.rights_role_test_case import RightsRoleGraphQLTestCase
from core.test_helpers import (
    create_clerk_role,
    create_enrolment_officer_role,
    create_raf_role,
    create_right_only_user,
    create_role_user,
    create_test_officer,
)
from insuree.test_helpers import create_test_insuree
from location.test_helpers import create_basic_test_locations, create_test_village
from policy.test_helpers import create_test_policy
from product.test_helpers import create_test_product


PREMIUMS_QUERY = """
query {
  premiums(first: 5) {
    edges { node { id uuid amount } }
  }
}
"""


class ContributionRightsTests(RightsRoleGraphQLTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_basic_test_locations()
        cls.village = create_test_village()
        cls.insuree = create_test_insuree(with_family=True, is_head=True)
        cls.product = create_test_product("CNTR")
        cls.policy = create_test_policy(cls.product, cls.insuree, link=True, valid=True)
        create_test_premium(policy_id=cls.policy.id)
        cls.districts = cls.DISTRICT_CODES + [cls.village.parent.parent.code]

    def _user(self, name, perms):
        return create_right_only_user(name, perms, district_codes=self.districts)

    def test_query_premiums_right(self):
        allowed = self._user("r_pr_q", ["gql_query_premiums_perms"])
        denied = self._user("r_pr_q_no", [])
        self.assert_gql_ok(allowed, PREMIUMS_QUERY)
        self.assert_gql_unauthorized(denied, PREMIUMS_QUERY)

    def test_create_update_delete_premiums_rights(self):
        allowed = self._user(
            "r_pr_c",
            [
                "gql_mutation_create_premiums_perms",
                "gql_mutation_update_premiums_perms",
                "gql_mutation_delete_premiums_perms",
            ],
        )
        denied = self._user("r_pr_c_no", [])
        mid = str(uuid.uuid4())
        create_mut = f"""
        mutation {{
          createPremium(input: {{
            clientMutationId: "{mid}"
            clientMutationLabel: "rights create premium"
            receipt: "RGT{mid[:6]}"
            payDate: "2023-12-13"
            payType: "C"
            isPhotoFee: false
            amount: "100"
            policyUuid: "{self.policy.uuid}"
          }}) {{ clientMutationId internalId }}
        }}
        """
        self.assert_mutation_permitted(allowed, create_mut, mid)
        mid_no = str(uuid.uuid4())
        self.assert_mutation_unauthorized(denied, create_mut.replace(mid, mid_no), mid_no)


class ContributionRoleTests(RightsRoleGraphQLTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_basic_test_locations()
        cls.village = create_test_village()
        cls.insuree = create_test_insuree(with_family=True, is_head=True)
        cls.product = create_test_product("CNTR2")
        cls.policy = create_test_policy(cls.product, cls.insuree, link=True, valid=True)
        create_test_premium(policy_id=cls.policy.id)
        cls.districts = cls.DISTRICT_CODES + [cls.village.parent.parent.code]
        cls.officer = create_test_officer(
            villages=[cls.village], custom_props={"code": "CNTEO"}
        )
        cls.users = {
            "clerk": create_role_user(
                "cnt_clk", create_clerk_role(), district_codes=cls.districts
            ),
            "enrolment_officer": create_role_user(
                "cnt_eo",
                create_enrolment_officer_role(),
                district_codes=cls.districts,
                officer=cls.officer,
            ),
            "raf": create_role_user(
                "cnt_raf", create_raf_role(), district_codes=cls.districts
            ),
        }

    def test_roles_can_query_premiums(self):
        for name, user in self.users.items():
            with self.subTest(role=name):
                self.assert_user_has_named_perms(user, ["gql_query_premiums_perms"])
                self.assert_gql_ok(user, PREMIUMS_QUERY)

    def test_clerk_and_eo_can_create_premiums(self):
        for name in ("clerk", "enrolment_officer"):
            with self.subTest(role=name):
                self.assert_user_has_named_perms(
                    self.users[name], ["gql_mutation_create_premiums_perms"]
                )
