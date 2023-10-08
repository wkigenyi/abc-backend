from django.db import models

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# Create your models here.
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

class Recon(models.Model):
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
    


