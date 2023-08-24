from contribution.reports import premium_collection, payment_category_overview
from contribution.reports.payment_category_overview import payment_category_overview_query
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
    {
        "name": "payment_category_overview",
        "engine": 0,
        "default_report": payment_category_overview.template,
        "description": "Payment category overview",
        "module": "contribution",
        "python_query": payment_category_overview_query,
        "permission": ["131211"],
    },
]
