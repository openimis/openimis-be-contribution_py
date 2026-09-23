from django.apps import AppConfig

from core.rights_declaration import RightsDeclaration

MODULE_NAME = "contribution"


# Rights, by entity then by action. The entity is the contribution (Premium).
DJANGO_PERMS = {
    "premium": {
        "query": ("contribution.view_premium", 101301),
        "create": ("contribution.add_premium", 101302),
        "update": ("contribution.change_premium", 101303),
        "delete": ("contribution.delete_premium", 101304),
    },
}

_PERM_CFG = {
    "gql_query_premiums_perms": ("premium", "query"),
    "gql_mutation_create_premiums_perms": ("premium", "create"),
    "gql_mutation_update_premiums_perms": ("premium", "update"),
    "gql_mutation_delete_premiums_perms": ("premium", "delete"),
}

RIGHTS = RightsDeclaration(MODULE_NAME, DJANGO_PERMS, _PERM_CFG)

perms = RIGHTS.perms
django_perms = RIGHTS.django_perm_names
configured_perms = RIGHTS.configured
require = RIGHTS.require


DEFAULT_CFG = {
}


class ContributionConfig(AppConfig):
    name = MODULE_NAME

    # Rights: constants, no longer overridable. They go neither through DEFAULT_CFG
    # nor through ready(): `ModuleConfiguration.get_or_default` now ignores any
    # `_perms` key stored in the database.
    gql_query_premiums_perms = RIGHTS.perms("premium", "query")
    gql_mutation_create_premiums_perms = RIGHTS.perms("premium", "create")
    gql_mutation_update_premiums_perms = RIGHTS.perms("premium", "update")
    gql_mutation_delete_premiums_perms = RIGHTS.perms("premium", "delete")

    def __load_config(self, cfg):
        for field in cfg:
            if hasattr(ContributionConfig, field):
                setattr(ContributionConfig, field, cfg[field])

    def ready(self):
        from core.models import ModuleConfiguration
        cfg = ModuleConfiguration.get_or_default(MODULE_NAME, DEFAULT_CFG)
        self.__load_config(cfg)
