# Generated by Django 3.2.19 on 2023-07-18 11:55
from django.conf import settings
from django.db import migrations, models

from contribution.utils import AddFieldPostgres


class Migration(migrations.Migration):
    dependencies = [
        ('contribution', '0003_alter_premium_options'),
    ]

    # For MSSQL These changes were added through raw sql, to keep consistency with existing databases it couldn't be
    # changed in postgres sql script.
    operations = []
    if not settings.MSSQL:
        operations = [
            AddFieldPostgres(
                model_name='premium',
                name='all_details_commission_report',
                field=models.DateTimeField(blank=True, db_column='AllDetailsCommissionReport', null=True),
            ),
            AddFieldPostgres(
                model_name='premium',
                name='overview_commission_report',
                field=models.DateTimeField(blank=True, db_column='OverviewCommissionReport', null=True),
            ),
            AddFieldPostgres(
                model_name='premium',
                name='reporting_commission_id',
                field=models.IntegerField(blank=True, db_column='ReportingCommissionID', null=True),
            )
        ]