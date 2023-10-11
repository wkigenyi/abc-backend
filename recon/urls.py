# from .views import ExceptionsView, ReconStatsView, ReconcileView, ReconciledDataView, ReversalsView, UnReconciledDataView,UploadedFilesViewset
from rest_framework.routers import DefaultRouter
from django.urls import path,include

from .views import ReconcileView, UploadedFilesViewset

router = DefaultRouter()
router.register("files",UploadedFilesViewset,basename="files")

urlpatterns = [
    path("api/",include(router.urls)),
    path('api/reconcile/', ReconcileView.as_view(), name='reconcile'),
    # path('api/reconstats/<str:Swift_code_up>/', ReconStatsView.as_view(), name='reconstats'),
    # path('api/reversals/<str:swift_code_up>/', ReversalsView.as_view(), name='reversals'),
    # path('api/exceptions/<str:swift_code_up>/', ExceptionsView.as_view(), name='exceptions'),
    # path('api/reconcileddata/', ReconciledDataView.as_view(), name='reconcileddata'),
    # path('api/unreconcileddata/', UnReconciledDataView.as_view(), name='unreconcileddata'),
    # path('reconcile/', ReconcileView.as_view(), name='reconcile'),
    # path('reconstats/<str:Swift_code_up>/', ReconStatsView.as_view(), name='reconstats'),
    # path('reversals/<str:swift_code_up>/', ReversalsView.as_view(), name='reversals'),  # Add this line
    # path('exceptions/<str:swift_code_up>/', ExceptionsView.as_view(), name='exceptions'),
    # path('reconcileddata/', ReconciledDataView.as_view(), name='reconcileddata'),
    # path('unreconcileddata/', UnReconciledDataView.as_view(), name='unreconcileddata'),
    # path('settlementcsv_files/', SettlementView.as_view(), name='settlement-csv-files'),
    # path('sabsreconcile_csv_file/', sabsreconcile_csv_filesView.as_view(), name='ssabsreconcile_csv_file'),
    # path('upload/', view_function, name='upload_excel'),
    # path('settle/<str:batch>/', combine_transactions, name='combine_transactions'),

]