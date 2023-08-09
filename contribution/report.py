from claim.reports import claim_percentage_referrals
from claim.reports.claim_percentage_referrals import claim_percentage_referrals_query
from contribution.reports import premium_collection
from contribution.reports.premium_collection import premium_collection_query

report_definitions = [
    {
        "name": "premium_collection",
        "engine": 0,
        "default_report": premium_collection.template,
        "description": "Premium collection",
        "module": "contribution",
        "python_query": premium_collection_query,
        "permission": ["131204"],
    },
]
