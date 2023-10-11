# utils.py
from .models import ReconciliationLog, Transactions,Reconciliation
from django.http import Http404,JsonResponse,FileResponse
from django.shortcuts import render,redirect
from datetime import datetime
from django.db.models import F, Q, Case, When, Value, CharField

from django.http import JsonResponse
from django.db.models.functions import Now
from django.db.models import Min, Max


from django.http import JsonResponse
import pandas as pd
import math
import re
import logging

# Helper functions
def clean_amount(value):
    try:
        # Convert the value to a float and then to an integer to remove decimals
        return str(int(float(value)))
    except:
        return '0'  # Default to '0' if conversion fails

def remo_spec_x(value):
    cleaned_value = re.sub(r'[^0-9a-zA-Z]', '', str(value))
    if cleaned_value == '':
        return '0'
    return cleaned_value

def pad_strings_with_zeros(input_str):
    if len(input_str) < 12:
        num_zeros = 12 - len(input_str)
        padded_str = '0' * num_zeros + input_str
        return padded_str
    else:
        return input_str[:12]

def clean_date(value):
    try:
        # Convert to datetime to ensure it's in datetime format
        date_value = pd.to_datetime(value).date()
        return str(date_value).replace("-", "")
    except:
        return value  # Return the original value if conversion fails

# Main pre-processing function
def pre_processing(df):
    # Cleaning logic
    for column in df.columns:
        # Cleaning for date columns
        if column in ['Date', 'DATE_TIME']:
            df[column] = df[column].apply(clean_date)
        # Cleaning for amount columns
        elif column in ['Amount', 'AMOUNT']:
            df[column] = df[column].apply(clean_amount)
        else:
            df[column] = df[column].apply(remo_spec_x)  # Clean without converting to string
        
        # Padding for specific columns
        if column in ['ABC Reference', 'TRN_REF']:
            df[column] = df[column].apply(pad_strings_with_zeros)
    
    return df

def unserializable_floats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert unserializable floats (NaN, Infinity) to string representations.
    """
    df = df.replace({math.nan: "NaN", math.inf: "Infinity", -math.inf: "-Infinity"})
    return df

def setlement_reconciliation(DF1: pd.DataFrame, DF2: pd.DataFrame) -> (pd.DataFrame, pd.DataFrame, pd.DataFrame):
    """
    Perform reconciliation between two dataframes and return the merged results.
    """
    # Merge the dataframes on the relevant columns
    merged_setle = DF1.merge(DF2, on=['DATE_TIME', 'TRN_REF'], how='outer', suffixes=('_DF1', '_DF2'), indicator=True)
    
    # Calculate the differences for amount and commission columns
    merged_setle.loc[merged_setle['_merge'] == 'both', 'AMOUNT_DIFF'] = (
        pd.to_numeric(merged_setle['AMOUNT_DF1'], errors='coerce') - 
        pd.to_numeric(merged_setle['AMOUNT_DF2'], errors='coerce')
    )

    merged_setle.loc[merged_setle['_merge'] == 'both', 'ABC_COMMISSION_DIFF'] = (
        pd.to_numeric(merged_setle['ABC_COMMISSION_DF1'], errors='coerce') - 
        pd.to_numeric(merged_setle['ABC_COMMISSION_DF2'], errors='coerce')
    )
    
    # Assign reconciliation status
    merged_setle['Recon Status'] = 'Unreconciled'    
    merged_setle.loc[merged_setle['_merge'] == 'both', 'Recon Status'] = 'Reconciled'
    
    # Separate dataframes based on the reconciliation status
    matched_setle = merged_setle[merged_setle['Recon Status'] == 'Reconciled']
    unmatched_setle = merged_setle[merged_setle['Recon Status'] == 'Unreconciled']
    unmatched_setlesabs = merged_setle[(merged_setle['AMOUNT_DIFF'] != 0) | (merged_setle['ABC_COMMISSION_DIFF'] != 0)]
    
    # Define columns to keep
    use_columns = ['TRN_REF', 'DATE_TIME', 'BATCH_DF1', 'TXN_TYPE_DF1', 'AMOUNT_DF1', 
                            'FEE_DF1', 'ABC_COMMISSION_DF1', 'AMOUNT_DIFF', 'ABC_COMMISSION_DIFF', 
                            '_merge', 'Recon Status']

    # Filter columns
    merged_setle = merged_setle[use_columns]    
    matched_setle = matched_setle[use_columns]
    unmatched_setle = unmatched_setle[use_columns]
    unmatched_setlesabs = unmatched_setlesabs[use_columns]

    return merged_setle, matched_setle, unmatched_setle, unmatched_setlesabs

def read_batch_file(file_path, sheet_name):
    """
    Read an Excel file into a DataFrame.
    """
    try:
        with pd.ExcelFile(file_path) as xlsx:
            df = pd.read_excel(xlsx, sheet_name=sheet_name, usecols=[0, 1, 2, 7, 8, 9, 11], skiprows=0)
        # Rename columns
        df.columns = ['TRN_REF', 'DATE_TIME', 'BATCH', 'TXN_TYPE', 'AMOUNT', 'FEE', 'ABC_COMMISSION']
        return df
    except Exception as e:
        logging.error(f"An error occurred while opening the Excel file: {e}")
        return None

def pre_processing_amt(df):
    """
    Pre-process amount columns in the dataframe.
    """
    def clean_amount(value):
        try:
            # Convert value to float and round
            return round(float(value))
        except:
            return value  # Return original value if conversion fails
    
    # Clean amount columns
    for column in ['AMOUNT', 'FEE', 'ABC_COMMISSION']:
        df[column] = df[column].apply(clean_amount)
    
    return df

def batch_query(batch):
    try:
        # Fetch data using Django ORM
        transactions = Transactions.objects.filter(
            RESPONSE_CODE='0',
            BATCH=batch,
            ISSUER_CODE__ne='730147',  # Note: '__ne' is Django's ORM way to specify "not equal"
            TXN_TYPE__nin=['ACI', 'AGENTFLOATINQ'],  # Note: '__nin' stands for "not in"
            REQUEST_TYPE__nin=['1420', '1421']
        ).values(
            'DATE_TIME', 'TRN_REF', 'BATCH', 'TXN_TYPE', 'ISSUER', 
            'ACQUIRER', 'AMOUNT', 'FEE', 'ABC_COMMISSION'
        )

        # Convert to DataFrame
        datafile = pd.DataFrame.from_records(transactions)

        return datafile
    except Exception as e:
        logging.error(f"Error fetching data from the database: {str(e)}")
        return None

def add_payer_beneficiary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds 'Payer' and 'Beneficiary' columns to the DataFrame.

    :param df: Input DataFrame.
    :return: DataFrame with 'Payer' and 'Beneficiary' columns added.
    """
    df['Payer'] = df['ACQUIRER']
    df['Beneficiary'] = df['ISSUER']
    return df

def convert_batch_to_int(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts the 'BATCH' column to numeric, rounds it to the nearest integer, and fills NaN with 0.

    :param df: DataFrame containing the 'BATCH' column to convert.
    :return: DataFrame with the 'BATCH' column converted.
    """
    # Check data type and convert 'BATCH' column to numeric
    df['BATCH'] = pd.to_numeric(df['BATCH'], errors='coerce')
    # Apply the round method
    df['BATCH'] = df['BATCH'].round(0).fillna(0).astype(int)
    
    return df

# =========================
# Functions from db_exceptions dj.py
# =========================
def select_exceptions(bank_id):
    # Use Django ORM to filter and get the exceptions
        excep_results = Reconciliation.objects.filter(
            Q(EXCEP_FLAG__isnull=False),
            Q(ISSUER_CODE=bank_id) | Q(ACQUIRER_CODE=bank_id)
        ).values(
            'DATE_TIME', 'TRAN_DATE', 'TRN_REF', 'BATCH', 'ACQUIRER_CODE', 'ISSUER_CODE', 'EXCEP_FLAG'
        )

        # Create the RECON_STATUS field based on ACQ_FLG and ISS_FLG values
        for result in excep_results:
            if result['ACQ_FLG'] == 1 or result['ISS_FLG'] == 1:
                result['RECON_STATUS'] = 'Partly Reconciled'
            elif result['ACQ_FLG'] == 1 and result['ISS_FLG'] == 1:
                result['RECON_STATUS'] = 'Fully Reconciled'

        return excep_results    
        
# =========================
# Functions from db_recon_data dj.py
# =========================
# Configuring logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def update_reconciliation(df, bank_id):

    if df.empty:
        logging.warning("No Records to Update.")
        return

    update_count = 0
    insert_count = 0

    for index, row in df.iterrows():
        date_time = row['DATE_TIME']
        batch = row['BATCH']
        trn_ref = row['TRN_REF2']
        issuer_code = row['ISSUER_CODE']
        acquirer_code = row['ACQUIRER_CODE']

        if pd.isnull(trn_ref):
            logging.warning(f"Empty Trn Reference for {index}.")
            continue

        # Fetching existing data
        existing_data = Reconciliation.objects.filter(TRN_REF=trn_ref)

        if existing_data.exists():
            # If already existing, just update
            try:
                existing_data.update(
                    ISS_FLG=1 if issuer_code == bank_id else 0,
                    ACQ_FLG=1 if acquirer_code == bank_id else 0,
                    ISS_FLG_DATE=datetime.now() if issuer_code == bank_id else None,
                    ACQ_FLG_DATE=datetime.now() if acquirer_code == bank_id else None
                )
                update_count += 1
            except Exception as err:
                logging.error(f"Error updating TRN_REF '{trn_ref}': {err}")
        else:
            # If not existing, insert and then update
            try:
                with Transactions.atomic():
                    new_record = Reconciliation(
                        DATE_TIME=datetime.now(),
                        TRAN_DATE=date_time,
                        TRN_REF=trn_ref,
                        BATCH=batch,
                        ACQUIRER_CODE=acquirer_code,
                        ISSUER_CODE=issuer_code
                    )
                    new_record.save()
                    insert_count += 1
                    # Immediate update after insert
                    new_record.ISS_FLG = 1 if issuer_code == bank_id else 0
                    new_record.ACQ_FLG = 1 if acquirer_code == bank_id else 0
                    new_record.ISS_FLG_DATE = datetime.now() if issuer_code == bank_id else None
                    new_record.ACQ_FLG_DATE = datetime.now() if acquirer_code == bank_id else None
                    new_record.save()
            except Exception as err:
                logging.error(f"Error processing PK '{trn_ref}': {err}")

    if update_count == 0:
        logging.info("No new records were updated.")
    if insert_count == 0:
        logging.info("No new records were inserted.")

    feedback = f"Updated: {update_count}, Inserted: {insert_count}"
    logging.info(feedback)

    return feedback

# =========================
# Functions from db_recon_stats dj.py
# =========================
def insert_recon_stats(bank_id, user_id, reconciled_rows, unreconciled_rows, exceptions_rows, feedback, 
                       requested_rows, uploaded_rows, date_range_str):
    new_log = ReconciliationLog(
        DATE_TIME = datetime.now(),  # This will automatically set the current date and time
        BANK_ID = bank_id,
        USER_ID = user_id,
        RECON_RWS = reconciled_rows,
        UNRECON_RWS = unreconciled_rows,
        EXCEP_RWS = exceptions_rows,
        FEEDBACK = feedback,
        RQ_RWS = requested_rows,
        UPLD_RWS = uploaded_rows,
        RQ_DATE_RANGE = date_range_str
    )
    new_log.save()

def recon_logs_req(bank_id):
    # Querying the ReconciliationLog table based on BANK_ID
    logs = ReconciliationLog.objects.filter(BANK_ID = bank_id)
    # This will return a QuerySet, you can iterate over it or convert it to a list
    return logs

# =========================
# Functions from db_reversals dj.py
# =========================
def select_reversals(bank_id):
    try:
        transactions = Transactions.objects.annotate(
            FIRST_REQUEST=F('REQUEST_TYPE'),
            FIRST_LEG_RESP=Case(
                When(
                    condition=Q(TRAN_STATUS_0__in=['0']),
                    then=Value('Successful')
                ),
                default=Value('Failed'),
                output_field=CharField(),
            ),
            SECND_LEG_RESP=Case(
                When(
                    condition=Q(TRAN_STATUS_1__in=['0']),
                    then=Value('Successful')
                ),
                default=Value('Failed'),
                output_field=CharField(),
            ),
            REV_STATUS=Case(
                When(
                    condition=Q(RESPONSE_CODE__in=['0']),
                    then=Value('Successful')
                ),
                default=Value('Failed'),
                output_field=CharField(),
            ),
            ELAPSED_TIME=Case(
                When(
                    condition=Q(RESPONSE_CODE__in=['0']),
                    then=None
                ),
                default=F('DATE_TIME') - Now(),
                output_field=CharField(),
            ),
            REVERSAL_TYPE=Case(
                When(
                    condition=Q(REQUEST_TYPE='1420'),
                    then=Value('First Reversal')
                ),
                When(
                    condition=Q(REQUEST_TYPE='1421'),
                    then=Value('Repeat Reversal')
                ),
                default=Value('Unknown'),
                output_field=CharField(),
            )
        ).filter(
            Q(REQUEST_TYPE='1200'),
            Q(TRAN_STATUS_1__isnull=False),
            Q(TRAN_STATUS_0__isnull=False),
            (
                (Q(TRAN_STATUS_0__in=['0', '00']) & ~Q(TRAN_STATUS_1__in=['null', '00', '0'])) |
                (Q(TRAN_STATUS_1__in=['0', '00']) & ~Q(TRAN_STATUS_0__in=['null', '00', '0']))
            ),
            Q(TXN_TYPE__in=['ACI', 'AGENTFLOATINQ', 'BI', 'MINI']),
            Q(ISSUER_CODE=bank_id) | Q(ACQUIRER_CODE=bank_id)
        ).values(
            'DATE_TIME', 'TRN_REF', 'TXN_TYPE', 'ISSUER', 'ACQUIRER', 'AMOUNT',
            'FIRST_REQUEST', 'AGENT_CODE', 'FIRST_LEG_RESP', 'SECND_LEG_RESP',
            'REV_STATUS', 'ELAPSED_TIME', 'REVERSAL_TYPE'
        ).order_by('DATE_TIME', 'TRN_REF')

        return transactions
    except Exception as e:
        logging.error(f"Error fetching data from the database: {str(e)}")
        return None

# =========================
# Functions from setle_sabs dj.py & setlement_ .py
# =========================
    
def setleSabs(request, batch):

    try:
        # Assuming you have a function batch_query() that interacts with Django's ORM
        datadump = batch_query(batch)

        # Check if datadump is not None and not empty
        if datadump is not None and not datadump.empty:         
            datadump = pre_processing_amt(datadump)
            datadump = pre_processing(datadump)
        else:
            logging.info("No records for processing found.")

        # Get the uploaded file from request
        uploaded_file = request.FILES.get('file')

        if uploaded_file:
            # Read the uploaded Excel file into a pandas DataFrame
            SABSfile_ = pd.read_excel(uploaded_file)

            SABSfile_ = pre_processing_amt(SABSfile_)
            SABSfile_ = pre_processing(SABSfile_)
        else:
            logging.error("No uploaded Excel file found.")

        merged_setle, matched_setle, unmatched_setle, unmatched_setlesabs = setlement_reconciliation(SABSfile_, datadump)

        # Use Django's logging mechanism
        logging.info('Thank you, your settlement Report is ready')

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({
        'merged_setle': merged_setle.to_dict(),
        'matched_setle': matched_setle.to_dict(),
        'unmatched_setle': unmatched_setle.to_dict(),
        'unmatched_setlesabs': unmatched_setlesabs.to_dict()
    })
# =========================
# Functions from mainFile.py
# =========================
def update_exception_flag(df, bank_id):

    if df.empty:
        logging.warning("No Exceptions Records to Update.")
        return

    update_count = 0

    for index, row in df.iterrows():
        trn_ref = row['trn_ref']

        if pd.isnull(trn_ref):
            logging.warning(f"Empty Exceptions Trn Reference for {index}.")
            continue

        try:
            # Using Django's ORM to achieve the update
            updated_records = Reconciliation.objects.filter(TRN_REF=trn_ref).update(
                EXCEP_FLAG=Case(
                    When(Q(EXCEP_FLAG__isnull=True) | Q(EXCEP_FLAG=0) | ~Q(EXCEP_FLAG=1),
                         Q(ISSUER_CODE=bank_id) | Q(ACQUIRER_CODE=bank_id), 
                         then=Value('Y')),
                    default=Value('N')
                )
            )

            update_count += updated_records
        except Exception as err:  # Catch more generic exceptions since we're not using pyodbc directly
            logging.error(f"Error updating PK '{trn_ref}': {err}")

    if update_count == 0:
        logging.info("No Exceptions were updated.")

    exceptions_feedback = f"Updated: {update_count}"
    logging.info(exceptions_feedback)

    return exceptions_feedback


def use_cols(queryset):
    """
    Process a queryset from the Transaction model, renaming and selecting specific fields.

    :param queryset: QuerySet to be processed.
    :return: DataFrame with selected and renamed columns.
    """
    # Annotate the queryset with the renamed fields and any calculated fields
    queryset = queryset.annotate(
        DATE_TIME=F('date_time'),
        AMOUNT=F('amount'),
        TRN_REF2=F('original_trn_ref'),
        BATCH=F('batch'),
        TXN_TYPE=F('txn_type_y'),
        ISSUER_CODE=F('issuer_code'),
        ACQUIRER_CODE=F('acquirer_code'),
        RESPONSE_CODE=F('response_code'),
        Recon_Status=Value('Unreconciled')
    )

    # Convert the QuerySet to a DataFrame for further processing
    df = pd.DataFrame(list(queryset.values(
        'DATE_TIME', 'AMOUNT', 'TRN_REF2', 'BATCH', 'TXN_TYPE', 
        'ISSUER_CODE', 'ACQUIRER_CODE', 'RESPONSE_CODE', 'Recon_Status'
    )))

    # Convert 'DATE_TIME' to datetime
    df['DATE_TIME'] = pd.to_datetime(df['DATE_TIME'])

    return df

def backup_refs(queryset, reference_column):
    # Backup the original reference column
    queryset = queryset.annotate(**{f'Original_{reference_column}': F(reference_column)})
    return queryset

def date_range(queryset, date_column):
    min_date = queryset.aggregate(Min(date_column))[date_column + '__min']
    max_date = queryset.aggregate(Max(date_column))[date_column + '__max']
    return min_date.strftime('%Y-%m-%d'), max_date.strftime('%Y-%m-%d')

def unserializable_floats(queryset):
    # Convert the QuerySet to DataFrame and then perform the replacement
    df = pd.DataFrame(list(queryset.values()))
    df = df.replace({math.nan: "NaN", math.inf: "Infinity", -math.inf: "-Infinity"})
    return df

# =========================
# Django Views
# =========================
def fetch_exceptions(request, bank_id):
    results = select_exceptions(bank_id)
    return JsonResponse(list(results), safe=False)

def upld_view_function(request):
    # Ensure it's a POST request and a file has been uploaded
    if request.method == 'POST' and 'file' in request.FILES:
        uploaded_file = request.FILES['file']

        # Read the uploaded Excel file into a pandas DataFrame
        raw_data = pd.read_excel(uploaded_file)

        # Process the data using pre_processing function
        cleaned_data = pre_processing(raw_data)

        # Continue with your logic, e.g., save to database, return a response, etc.
        # Here, I'm returning the cleaned data's shape as a JSON response for illustration
        return JsonResponse({
            'rows': cleaned_data.shape[0],
            'columns': cleaned_data.shape[1]
        })

    # If not POST or no file, return an error response
    return JsonResponse({'error': 'Invalid request or no file uploaded'}, status=400)

def batch_view_function(request):
    # Ensure the request is POST and contains an uploaded file
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST requests are allowed."}, status=400)
    
    uploaded_file = request.FILES.get('file')
    
    if not uploaded_file:
        return JsonResponse({"error": "No file was uploaded."}, status=400)

    # Read the uploaded Excel file
    try:
        raw_data = read_batch_file(uploaded_file.path, 'SheetName')  # Replace 'SheetName' with your actual sheet name
    except Exception as e:
        return JsonResponse({"error": f"Error reading the Excel file: {str(e)}"}, status=500)
    
    # Pre-process the data
    cleaned_data = pre_processing_amt(raw_data)

    # Assume there's another DataFrame DF2 you want to reconcile with cleaned_data
    # For the purpose of this example, I'm just using cleaned_data for both DFs
    # You can replace this logic with actual data retrieval and processing
    DF2 = cleaned_data  
    merged_setle, matched_setle, unmatched_setle, unmatched_setlesabs = setlement_reconciliation(cleaned_data, DF2)

    # Convert dataframes to a format suitable for JSON serialization
    merged_setle = unserializable_floats(merged_setle).to_dict(orient='records')
    matched_setle = unserializable_floats(matched_setle).to_dict(orient='records')
    unmatched_setle = unserializable_floats(unmatched_setle).to_dict(orient='records')
    unmatched_setlesabs = unserializable_floats(unmatched_setlesabs).to_dict(orient='records')

    # Return a structured JsonResponse
    return JsonResponse({
        "success": True,
        "merged_setle": merged_setle,
        "matched_setle": matched_setle,
        "unmatched_setle": unmatched_setle,
        "unmatched_setlesabs": unmatched_setlesabs
    })

def combine_transactions(request, batch):
    """
    Django view function for the settle operation.
    """

    try:
        logging.basicConfig(filename='settlement.log', level=logging.ERROR)

        # Execute the batch query
        datadump = batch_query(batch)
        
        if datadump is not None and not datadump.empty:         
            datadump = convert_batch_to_int(datadump)
            datadump = pre_processing_amt(datadump)
            datadump = add_payer_beneficiary(datadump)            
        else:
            logging.warning("No records for processing found.")
            return JsonResponse({"error": "No records for processing found."}, status=404)

        setlement_result = combine_transactions(datadump, acquirer_col='Payer', issuer_col='Beneficiary', amount_col='AMOUNT', type_col='TXN_TYPE')

        # Convert the result to a format suitable for JSON response
        setlement_result_dict = setlement_result.to_dict(orient='records')
        return JsonResponse({"result": setlement_result_dict})

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)
    
def db_transactions(min_date, max_date, bank_id):
    """
    Fetches transactions from the database based on the given criteria.

    :param min_date: The start date for the transactions.
    :param max_date: The end date for the transactions.
    :param bank_id: The swift code to filter transactions.
    :return: A pandas DataFrame containing the transactions.
    """
    # Filter the records based on the criteria
    transactions = Transactions.objects.filter(
        Q(ISSUER_CODE=bank_id) | Q(ACQUIRER_CODE=bank_id),
        DATE_TIME__date__range=[min_date, max_date],
        RESPONSE_CODE='0'
    ).exclude(
        AMOUNT=0,
        TXN_TYPE__in=['ACI','AGENTFLOATINQ','BI','MINI'],
        REQUEST_TYPE__in=['1420','1421']
    ).values(
        'DATE_TIME', 'BATCH', 'TRN_REF', 'TXN_TYPE', 'ISSUER_CODE', 'ACQUIRER_CODE', 'AMOUNT', 'RESPONSE_CODE'
    )

    # Convert the QuerySet to a pandas DataFrame
    df = pd.DataFrame.from_records(transactions)

    return df

# The process_reconciliation function remains mostly unchanged
def bank_reconciliation(DF1: pd.DataFrame, DF2: pd.DataFrame) -> (pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame):

    # Rename columns of DF1 to match DF2 for easier merging
    DF1 = DF1.rename(columns={'Date': 'DATE_TIME','ABC Reference': 'TRN_REF','Amount': 'AMOUNT','Transaction type': 'TXN_TYPE'})
    
    # Merge the dataframes on the relevant columns
    merged_df = DF1.merge(DF2, on=['DATE_TIME', 'TRN_REF', 'AMOUNT'], how='outer', indicator=True)
    
    # Create a new column 'Recon Status'
    merged_df['Recon Status'] = 'Unreconciled'
    merged_df.loc[(merged_df['Recon Status'] == 'Unreconciled') & (merged_df['RESPONSE_CODE'] == '0') | (merged_df['Response_code'] == '0'), 'Recon Status'] = 'succunreconciled'
    merged_df.loc[merged_df['_merge'] == 'both', 'Recon Status'] = 'Reconciled'

    # Separate the data into three different dataframes based on the reconciliation status
    reconciled_data = merged_df[merged_df['Recon Status'] == 'Reconciled']
    succunreconciled_data = merged_df[merged_df['Recon Status'] == 'succunreconciled']
    # unreconciled_data = merged_df[merged_df['Recon Status'] == 'Unreconciled']
    exceptions = merged_df[(merged_df['Recon Status'] == 'Reconciled') & (merged_df['RESPONSE_CODE'] != '0')]

    return merged_df, reconciled_data, succunreconciled_data, exceptions

def bank_reconciliation_view(request):
    # Check if this is a POST request and if 'file1' has been uploaded
    if request.method == 'POST' and 'file1' in request.FILES:
        file1 = request.FILES['file1']

        # Use pandas to read the uploaded Excel file into a dataframe
        DF1 = pd.read_excel(file1)

        # Extract the min and max dates from DF1 for querying the database
        min_date = DF1['Date'].min()
        max_date = DF1['Date'].max()

        # Assuming the Swift code is a parameter in the POST request
        bank_id = request.POST.get('bank_id')

        # Get the transactions from the database
        DF2 = db_transactions(min_date, max_date, bank_id)

        # Call the process_reconciliation function
        merged_df, reconciled_data, succunreconciled_data, exceptions = bank_reconciliation(DF1, DF2)

        # For simplicity, let's return the shape of each dataframe as a JsonResponse
        # (you can adjust this to your needs)
        return JsonResponse({
            "merged_df_shape": merged_df.shape,
            "reconciled_data_shape": reconciled_data.shape,
            "succunreconciled_data_shape": succunreconciled_data.shape,
            "exceptions_shape": exceptions.shape
        })
    else:
        # Handle the GET request or if no file is uploaded (you might want to render a template here)
        return JsonResponse({"message": "Please upload the required file."})



    


