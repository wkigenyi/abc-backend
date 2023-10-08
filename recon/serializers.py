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
        
class ReconcileSerializer(serializers.Serializer):
    file = serializers.FileField()
    swift_code = serializers.CharField(max_length=200)


class SabsSerializer(serializers.Serializer):
    file = serializers.FileField()
    batch_number = serializers.CharField(max_length=100)

class SettlementSerializer(serializers.Serializer):
    batch_number = serializers.CharField(max_length=100)