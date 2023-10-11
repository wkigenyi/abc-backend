from django.db import models

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# Create your models here.

class Transactions(models.Model):
    DATE_TIME = models.DateTimeField(null=True, blank=True)
    TRN_REF = models.CharField(max_length=255, null=True, blank=True)
    BATCH = models.CharField(max_length=255, null=True, blank=True)
    TXN_TYPE = models.CharField(max_length=255, null=True, blank=True)
    TXN_ID = models.CharField(max_length=255, null=True, blank=True)
    ISSUER = models.CharField(max_length=255, null=True, blank=True)
    ACQUIRER = models.CharField(max_length=255, null=True, blank=True)
    ISSUER_CODE = models.CharField(max_length=999, null=True, blank=True)
    ACQUIRER_CODE = models.CharField(max_length=999, null=True, blank=True)
    BRANCH_NAME = models.CharField(max_length=255, null=True, blank=True)
    AGENTNAMES = models.CharField(max_length=4000, null=True, blank=True)
    CHANNEL = models.CharField(max_length=255, null=True, blank=True)
    AGENT_CODE = models.CharField(max_length=255, null=True, blank=True)
    AGENT_CODE_ALIAS = models.CharField(max_length=255, null=True, blank=True)
    AMOUNT = models.DecimalField(max_digits=18, decimal_places=5, null=True, blank=True)
    ACC_NO = models.CharField(max_length=255, null=True, blank=True)
    STAN = models.CharField(max_length=255, null=True, blank=True)
    FEE = models.DecimalField(max_digits=18, decimal_places=5, null=True, blank=True)
    REQUEST_TYPE = models.CharField(max_length=255, null=True, blank=True)
    TRAN_REF_1 = models.CharField(max_length=255, null=True, blank=True)
    TRAN_REF_0 = models.CharField(max_length=255, null=True, blank=True)
    TRAN_STATUS_1 = models.CharField(max_length=255, null=True, blank=True)
    TRAN_STATUS_0 = models.CharField(max_length=255, null=True, blank=True)
    BENEFICIARY_ENTITY = models.CharField(max_length=255, null=True, blank=True)
    ISSUER_COMMISSION = models.DecimalField(max_digits=18, decimal_places=5, null=True, blank=True)
    ACQUIRER_COMMISSION = models.DecimalField(max_digits=18, decimal_places=5, null=True, blank=True)
    AGENT_COMMISSION = models.DecimalField(max_digits=18, decimal_places=5, null=True, blank=True)
    ABC_COMMISSION = models.DecimalField(max_digits=18, decimal_places=5, null=True, blank=True)
    RESPONSE_CODE = models.CharField(max_length=255, null=True, blank=True)
    TRANSACTION_STATUS = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        managed = False
        db_table = 'transactions'

class Bank(models.Model):
    name = models.CharField(max_length=50,unique=True)
    swift_code = models.CharField(max_length=10,unique=True)
    bank_code = models.CharField(max_length=10,null=True,unique=True)
    def __str__(self) -> str:
        return f"{self.name}"

class UserBankMapping(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE,primary_key=True)
    bank = models.ForeignKey(Bank,on_delete=models.CASCADE)
    def __str__(self) -> str:
        return f"{self.user.username}:{self.bank.name}"

class ReconciliationLog(models.Model):
    date_time = models.DateTimeField(db_column='DATE_TIME', blank=True, null=True)  # Field name made lowercase.
    recon_id = models.CharField(db_column='RECON_ID', max_length=35, blank=True, null=True)  # Field name made lowercase.
    bank_id = models.CharField(db_column='BANK_ID', max_length=15, blank=True, null=True)  # Field name made lowercase.
    user_id = models.CharField(db_column='USER_ID', max_length=35, blank=True, null=True)  # Field name made lowercase.
    rq_date_range = models.CharField(db_column='RQ_DATE_RANGE', max_length=255, blank=True, null=True)  # Field name made lowercase.
    upld_rws = models.CharField(db_column='UPLD_RWS', max_length=15, blank=True, null=True)  # Field name made lowercase.
    rq_rws = models.CharField(db_column='RQ_RWS', max_length=15, blank=True, null=True)  # Field name made lowercase.
    recon_rws = models.CharField(db_column='RECON_RWS', max_length=15, blank=True, null=True)  # Field name made lowercase.
    unrecon_rws = models.CharField(db_column='UNRECON_RWS', max_length=15, blank=True, null=True)  # Field name made lowercase.
    excep_rws = models.CharField(db_column='EXCEP_RWS', max_length=15, blank=True, null=True)  # Field name made lowercase.
    feedback = models.TextField(db_column='FEEDBACK', blank=True, null=True)  # Field name made lowercase. This field type is a guess.

    class Meta:
        managed = False
        db_table = 'Reconciliationlogs'

class Reconciliation(models.Model):
    date_time = models.DateTimeField(blank=True, null=True)  # Field name made lowercase.
    tran_date = models.DateTimeField(blank=True, null=True)  # Field name made lowercase.
    trn_ref = models.CharField(max_length=255, blank=True, null=True,unique=True)  # Field name made lowercase.
    batch = models.CharField(max_length=255, blank=True, null=True)  # Field name made lowercase.
    acquirer_code = models.CharField(max_length=255, blank=True, null=True)  # Field name made lowercase.
    issuer_code = models.CharField(max_length=255, blank=True, null=True)  # Field name made lowercase.
    excep_flag = models.CharField(max_length=6, blank=True, null=True)  # Field name made lowercase.
    acq_flg = models.CharField( max_length=6, blank=True, null=True)  # Field name made lowercase.
    iss_flg = models.CharField( max_length=6, blank=True, null=True)  # Field name made lowercase.
    acq_flg_date = models.DateTimeField( blank=True, null=True)  # Field name made lowercase.
    iss_flg_date = models.DateTimeField( blank=True, null=True)  # Field name made lowercase.
    last_modified_by_user = models.ForeignKey(User,on_delete=models.CASCADE,blank=True,null=True)

    def __str__(self) -> str:
        return self.trn_ref

def validate_file_extension(value):
    if(value.file.content_type not in ['application/vnd.ms-excel','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']):
        raise ValidationError(u'Wrong File Type')
class UploadedFile(models.Model):
    file = models.FileField(upload_to="uploaded_files")
    time = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User,on_delete=models.CASCADE,blank=True,null=True)
    def __str__(self) -> str:
        return self.file.name


    


