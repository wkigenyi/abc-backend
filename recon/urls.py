from .views import UploadedFilesViewset
from rest_framework.routers import DefaultRouter
from django.urls import path,include

router = DefaultRouter()
router.register("files",UploadedFilesViewset,basename="files")

urlpatterns = [
    path("api/",include(router.urls))
]