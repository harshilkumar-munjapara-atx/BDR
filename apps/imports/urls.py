from django.urls import path

from .views import ExcelConfirmImportView, ExcelPreviewView, SampleImportFileView

urlpatterns = [
    path("listings/import/preview/", ExcelPreviewView.as_view(), name="admin-import-preview"),
    path("listings/import/confirm/", ExcelConfirmImportView.as_view(), name="admin-import-confirm"),
    path("listings/import/sample/", SampleImportFileView.as_view(), name="admin-import-sample"),
]
