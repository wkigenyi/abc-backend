from django.contrib import admin
from .models import Bank,UserBankMapping,Reconciliation,UploadedFile

# Register your models here.
class BankAdmin(admin.ModelAdmin):
    list_display = ["name","swift_code"]

class MappedUserAdmin(admin.ModelAdmin):
    list_display = ["bank","user"]

class ReconciliationAdmin(admin.ModelAdmin):
    pass

class UploadedFilesAdmin(admin.ModelAdmin):
    list_display = ["file","time"]

admin.site.register(UserBankMapping,MappedUserAdmin)
admin.site.register(Bank,BankAdmin)
admin.site.register(Reconciliation,ReconciliationAdmin)
admin.site.register(UploadedFile,UploadedFilesAdmin)


