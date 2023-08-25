# Generated by Django 3.2.18 on 2023-05-12 12:15
import core.datetimes.ad_datetime
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contribution', '0002_add_premium_fields'),
        ('payer', '0001_initial'),
        ('policy', '0004_add_medical_oficer_reading_rights'),
    ]

        operations = [
              migrations.AddField(
                    model_name='premium',
                    name='all_details_commission_report',
                    field=models.DateTimeField(blank=True, db_column='AllDetailsCommissionReport', null=True),
                ),
                migrations.AddField(
                    model_name='premium',
                    name='overview_commission_report',
                    field=models.DateTimeField(blank=True, db_column='OverviewCommissionReport', null=True),
                ),
                migrations.AddField(
                    model_name='premium',
                    name='reporting_commission_id',
                    field=models.IntegerField(blank=True, db_column='ReportingCommissionID', null=True),
                ),
                migrations.AddField(
                    model_name='premium',
                    name='rowid',
                    field=models.TextField(blank=True, db_column='RowID', null=True),
                ),
                migrations.AddField(
                    model_name='premium',
                    name='source',
                    field=models.CharField(blank=True, db_column='Source', max_length=50, null=True),
                ),
                migrations.AddField(
                    model_name='premium',
                    name='source_version',
                    field=models.CharField(blank=True, db_column='SourceVersion', max_length=15, null=True),
                ),
    ]
    if settings.MSSQL:
        operations.append(
            migrations.AlterField(
                model_name='premium',
                name='created_date',
                field=models.DateTimeField(db_column='CreatedDate', default=core.datetimes.ad_datetime.AdDatetime.now),
            )
        

