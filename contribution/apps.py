from django.apps import AppConfig

MODULE_NAME = "contribution"

DEFAULT_CFG = {
    "gql_query_premiums_perms": ["101301"],
    "gql_query_payment_service_provider":   ["101305"],
    "gql_mutation_create_premiums_perms": ["101302"],
    "gql_mutation_update_premiums_perms": ["101303"],
    "gql_mutation_delete_premiums_perms": ["101304"],
    "gql_mutation_create_paymnet_service_provider" :  ["101306"],
    "gql_mutation_update_paymnet_service_provider" :  ["101307"],
    "gql_mutation_delete_paymnet_service_provider" :  ["101308"],
}


class ContributionConfig(AppConfig):
    name = MODULE_NAME

    gql_query_premiums_perms = []
    gql_query_payment_service_provider =   []
    gql_mutation_create_premiums_perms = []
    gql_mutation_update_premiums_perms = []
    gql_mutation_delete_premiums_perms = []
    gql_mutation_create_paymnet_service_provider =   []
    gql_mutation_update_paymnet_service_provider =   []
    gql_mutation_delete_paymnet_service_provider =   []

    def _configure_permissions(self, cfg):
        ContributionConfig.gql_query_premiums_perms = cfg["gql_query_premiums_perms"]
        ContributionConfig.gql_query_payment_service_provider  = cfg["gql_query_payment_service_provider"]
        ContributionConfig.gql_mutation_create_premiums_perms = cfg["gql_mutation_create_premiums_perms"]
        ContributionConfig.gql_mutation_update_premiums_perms = cfg["gql_mutation_update_premiums_perms"]
        ContributionConfig.gql_mutation_delete_premiums_perms = cfg["gql_mutation_delete_premiums_perms"]
        ContributionConfig.gql_mutation_create_paymnet_service_provider =   cfg["gql_mutation_create_paymnet_service_provider"]
        ContributionConfig.gql_mutation_update_paymnet_service_provider =   cfg["gql_mutation_update_paymnet_service_provider"]
        ContributionConfig.gql_mutation_delete_paymnet_service_provider =   cfg["gql_mutation_delete_paymnet_service_provider"]
    def ready(self):
        from core.models import ModuleConfiguration
        cfg = ModuleConfiguration.get_or_default(MODULE_NAME, DEFAULT_CFG)
        self._configure_permissions(cfg)
