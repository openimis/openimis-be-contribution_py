# Generated by Django 3.2.18 on 2023-05-12 12:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('policy', '0003_auto_20201021_0811'),
        ('payer', '0001_initial'),
        ('contribution', '0009_auto_20230503_1432'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='merchant_wallet',
            name='wallet_address',
        ),
    ]
