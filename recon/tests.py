
from django.http import Http404, JsonResponse
# from openpyxl import load_workbook
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import generics,status,viewsets

# from .models import Reconciliation, ReconciliationLog, UploadedFile
# from .serializers import ReconcileSerializer, UploadedFileSerializer

# from .utils import (select_exceptions,select_reversals,date_range, backup_refs, db_transactions, pre_processing,bank_reconciliation, recon_logs_req, unserializable_floats, use_cols, update_reconciliation,update_exception_flag, insert_recon_stats)
import pandas as pd

from .utils import backup_refs, pre_processing

# from utils import backup_refs, bank_reconciliation, db_transactions, insert_recon_stats, pre_processing, update_reconciliation, use_cols
# # import os

# # Create your views here.

# class ReconcileView(APIView):
#     serializer_class = ReconcileSerializer
#     # permission_classes = [IsAuthenticated]

#     def post(self, request):
#         serializer = self.serializer_class(data=request.data)
#         if serializer.is_valid():
#             uploaded_file = serializer.validated_data['file']
#             swift_code = serializer.validated_data['swift_code']

#             # Save the uploaded file temporarily
#             temp_file_path = "temp_file.xlsx"
            
#             with open(temp_file_path, "wb") as buffer:
#                 buffer.write(uploaded_file.read())
               

#             try:
#                 # Call the main function with the path of the saved file and the swift code
                
#                 result = reconcile_main_view(temp_file_path,swift_code)
#                 print(result)
#                 return result
                
#                 # return Response(result, status=status.HTTP_200_OK)

#             except Exception as e:
#                 # If there's an error during the process, ensure the temp file is removed
#                 if os.path.exists(temp_file_path):
#                     os.remove(temp_file_path)
                
#                 # Return error as response
#                 return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class UploadedFilesViewset(viewsets.ModelViewSet):
#     queryset = UploadedFile.objects.all()
#     serializer_class = UploadedFileSerializer
#     def create(self, request, *args, **kwargs):
#         user = request.user
#         file = request.FILES['file']
#         wb = load_workbook(file)
#         sheet = wb.get_sheet_by_name("Sheet1")
#         start_row = 2
#         count = 0
#         for _ in sheet.iter_rows(min_row=start_row,max_row=10):
#             row_no = start_row+count
#             time = sheet.cell(row_no,1).value
#             transaction_type = sheet.cell(row_no,2).value
#             amount = sheet.cell(row_no,3).value
#             abc_reference = sheet.cell(row_no,4).value
#             recon = Reconciliation(
#                 date_time=time,
#                 last_modified_by_user=user,
#                 trn_ref=abc_reference,
#                 )
#             recon.save()
#             print(time,transaction_type,amount,abc_reference)
#             count+=1
        
#         return super().create(request, *args, **kwargs) 

request = r'C:\Users\ISABIRYEDICKSON\Desktop\Python projects\datasets\Upload Template.xlsx'
bank_id = 130447
def reconcile_main_view(request,bank_id):

    # try:
        # uploaded_file = request.FILES.get('file')
        
        # Read the file into a DataFrame
        uploaded_df = pd.read_excel(request, usecols=[0, 1, 2, 3], skiprows=0)
        min_date, max_date = pd.date_range(uploaded_df, 'Date')

        uploaded_df = backup_refs(uploaded_df, 'ABC Reference')
        uploaded_df['Response_code'] = '0'
        UploadedRows = len(uploaded_df)
        
        uploaded_df_processed = pre_processing(uploaded_df)
        
#         # Using Django ORM or another function to fetch data instead of raw SQL
#         datadump = db_transactions(min_date, max_date, request.POST.get('bank_id'))
        
#         if datadump is not None:
#             datadump = backup_refs(datadump, 'TRN_REF')
#             requestedRows = len(datadump[datadump['RESPONSE_CODE'] == '0'])

#             # Clean and format columns in the datadump        
#             db_preprocessed = pre_processing(datadump)
                    
#             merged_df, reconciled_data, succunreconciled_data, exceptions = bank_reconciliation(uploaded_df_processed, db_preprocessed)  
#             succunreconciled_data = use_cols(succunreconciled_data) 
#             reconciled_data = use_cols(reconciled_data) 

#             feedback = update_reconciliation(reconciled_data, bank_id)
#             # exceptions_feedback = update_exception_flag(exceptions, bank_id)
            
#             insert_recon_stats(
#                 bank_id, len(reconciled_data), len(succunreconciled_data),
#                 len(exceptions), feedback, requestedRows, UploadedRows, min_date, max_date
#             )

#             # Return data as JSON or in another format you prefer
#             response_data = {
#                 'merged_data': merged_df.to_dict(),
#                 'reconciled_data': reconciled_data.to_dict(),
#                 'succunreconciled_data': succunreconciled_data.to_dict(),
#                 'exceptions': exceptions.to_dict(),
#                 'feedback': feedback,
#                 'requestedRows': requestedRows,
#                 'UploadedRows': UploadedRows,
#                 'date_range': f"{min_date},{max_date}"
#             }
#             print(response_data)
#             return response_data
#             # return JsonResponse(response_data)

#         else:
#             return JsonResponse({"error": "No data dump available."}, status=404)

#     except Exception as e:
#         return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)
    
# reconcile_main_view(request,bank_id)

# def ReconStats_req(request):
#     bank_id = request.GET.get('bank_id')  # Assuming you're passing bank_id as a GET parameter
#     if not bank_id:
#          return JsonResponse({'error': 'bank_id not provided'}, status=400)
    
#     logs_query = recon_logs_req(bank_id)
#     if logs_query is None:
#         return JsonResponse({'error': 'No records to display'}, status=500)
    
#     # Convert the QuerySet to a list of dictionaries
#     logs_list = list(logs_query.values())
    
#     return JsonResponse(logs_list, safe=False)

# class ReconStatsView(APIView):
    
#     def get(self, request, Swift_code_up):
            
#             try:
#                 # Assume recon_stats_req returns a list of dictionaries or None
#                 data = ReconStats_req(Swift_code_up)
#                 if data is None:
#                     return Response({'error': 'No data found'}, status=status.HTTP_404_NOT_FOUND)              
                
#                 return Response(data, status=status.HTTP_200_OK)

#             except Exception as e:
#                 return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
# def get_reversals(request):
#     bank_id = request.GET.get('bank_id')  # Assuming you're passing bank_id as a GET parameter
#     if not bank_id:
#         return JsonResponse({'error': 'bank_id not provided'}, status=400)
    
#     reversals_query = select_reversals(bank_id)
    
#     if reversals_query is None:
#         return JsonResponse({'error': 'No records to display'}, status=500)
    
#     # Convert the QuerySet to a list of dictionaries
#     reversals_list = list(reversals_query)
    
#     return JsonResponse(reversals_list, safe=False)

# class ReversalsView(APIView):
#     """
#     Retrieve reversal data.
#     """

#     def get(self, request, swift_code_up, *args, **kwargs):
#         # Use values from .env for database connection
#         data = get_reversals(swift_code_up)

#         # The data returned by select_reversals is assumed to be in a suitable format for JSON serialization

#         return Response(data, status=status.HTTP_200_OK)
    
# def get_exceptions(request):
#     bank_id = request.GET.get('bank_id')  # Assuming you're passing bank_id as a GET parameter
#     if not bank_id:
#         return JsonResponse({'error': 'bank_id not provided'}, status=400)
    
#     exceptions_query = select_exceptions(bank_id)
    
#     if exceptions_query is None:
#         return JsonResponse({'error': 'No records to display'}, status=500)
    
#     # Convert the QuerySet to a list of dictionaries and process RECON_STATUS
#     exceptions_list = []
#     for result in exceptions_query:
#         record = {
#             'DATE_TIME': result['DATE_TIME'],
#             'TRAN_DATE': result['TRAN_DATE'],
#             'TRN_REF': result['TRN_REF'],
#             'BATCH': result['BATCH'],
#             'ACQUIRER_CODE': result['ACQUIRER_CODE'],
#             'ISSUER_CODE': result['ISSUER_CODE'],
#             'EXCEP_FLAG': result['EXCEP_FLAG']
#         }
#         if result.get('ACQ_FLG') == 1 or result.get('ISS_FLG') == 1:
#             record['RECON_STATUS'] = 'Partly Reconciled'
#         elif result.get('ACQ_FLG') == 1 and result.get('ISS_FLG') == 1:
#             record['RECON_STATUS'] = 'Fully Reconciled'
#         exceptions_list.append(record)
    
#     return JsonResponse(exceptions_list, safe=False)

# class ExceptionsView(APIView):
#     """
#     Retrieve exceptions data.    """

#     def get(self, request, swift_code_up, *args, **kwargs):          

#         data = get_exceptions(swift_code_up)

#         # The data returned by select_exceptions is assumed to be in a suitable format for JSON serialization
#         return Response(data, status=status.HTTP_200_OK)

# class ReconciledDataView(APIView):
#     """
#     Retrieve reconciled data.
#     """

#     def get(self, request, *args, **kwargs):
#         global reconciled_data

#         if reconciled_data is not None:
#             reconciled_data_cleaned = unserializable_floats(reconciled_data)
#             data = reconciled_data_cleaned.to_dict(orient='records')
#             return Response(data, status=status.HTTP_200_OK)
#         else:
#             raise Http404("Reconciled data not found")

# # class UnReconciledDataView(APIView):
#     """
#     Retrieve unreconciled data.
#     """

#     def get(self, request, *args, **kwargs):
#         global succunreconciled_data

#         if succunreconciled_data is not None:
            
#             # reconciled_data_cleaned = unserializable_floats(reconciled_data)
#             # data = reconciled_data_cleaned.to_dict(orient='records')

#             unreconciled_data_cleaned = unserializable_floats(succunreconciled_data)
#             data =  unreconciled_data_cleaned.to_dict(orient='records')
#             return Response(data, status=status.HTTP_200_OK)
#         else:
#             raise Http404("Unreconciled data not found")  