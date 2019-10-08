import uuid
from django.db import models
from core import fields
from policy.models import Policy


class Premium(models.Model):
    id = models.AutoField(db_column='PremiumId', primary_key=True)
    uuid = models.CharField(db_column='PremiumUUID', max_length=36, default=uuid.uuid4, unique = True)
    legacy_id = models.IntegerField(
        db_column='LegacyID', blank=True, null=True)
    policy_id = models.ForeignKey(
        Policy, models.DO_NOTHING, db_column='PolicyID')
    # payer_id = models.ForeignKey(
    #     Tblpayer, models.DO_NOTHING, db_column='PayerID', blank=True, null=True)
    amount = models.DecimalField(
        db_column='Amount', max_digits=18, decimal_places=2)
    receipt = models.CharField(db_column='Receipt', max_length=50)
    pay_date = fields.DateField(db_column='PayDate')
    pay_type = models.CharField(db_column='PayType', max_length=1)
    is_photo_fee = models.BooleanField(
        db_column='isPhotoFee', blank=True, null=True)
    is_offline = models.BooleanField(
        db_column='isOffline', blank=True, null=True)
    reporting_id = models.IntegerField(
        db_column='ReportingId', blank=True, null=True)
    validity_from = fields.DateTimeField(db_column='ValidityFrom')
    validity_to = fields.DateTimeField(
        db_column='ValidityTo', blank=True, null=True)
    audit_user_id = models.IntegerField(db_column='AuditUserID')
    # rowid = models.TextField(db_column='RowID', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tblPremium'
