# Generated by Django 3.2.18 on 2023-05-12 12:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contribution', '0002_add_premium_fields'),
    ]
    if settings.MSSQL:
        operations = [
            migrations.AlterField(
                model_name='premium',
                name='created_date',
                field=models.DateTimeField(db_column='CreatedDate', default=core.datetimes.ad_datetime.AdDatetime.now),
            ),
        ]
    else:
        operations = []
