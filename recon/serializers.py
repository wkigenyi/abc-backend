from rest_framework import serializers
from .models import Bank,Recon,ReconciliationLog,UploadedFile

class ReconciliationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recon
        
class BankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bank

class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReconciliationLog

class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ["id","file"]