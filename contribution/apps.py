from django.apps import AppConfig

MODULE_NAME = "contribution"

DEFAULT_CFG = {
    "gql_query_premiums_perms": ["101301"],
    "gql_mutation_create_premiums_perms": ["101302"],
    "gql_mutation_update_premiums_perms": ["101303"],
    "gql_mutation_delete_premiums_perms": ["101304"],
}


class ContributionConfig(AppConfig):
    name = MODULE_NAME

    gql_query_premiums_perms = []
    gql_mutation_create_premiums_perms = []
    gql_mutation_update_premiums_perms = []
    gql_mutation_delete_premiums_perms = []

    def _configure_permissions(self, cfg):
        ContributionConfig.gql_query_premiums_perms = cfg["gql_query_premiums_perms"]
        ContributionConfig.gql_mutation_create_premiums_perms = cfg["gql_mutation_create_premiums_perms"]
        ContributionConfig.gql_mutation_update_premiums_perms = cfg["gql_mutation_update_premiums_perms"]
        ContributionConfig.gql_mutation_delete_premiums_perms = cfg["gql_mutation_delete_premiums_perms"]

    def ready(self):
        from core.models import ModuleConfiguration
        cfg = ModuleConfiguration.get_or_default(MODULE_NAME, DEFAULT_CFG)
        self._configure_permissions(cfg)
