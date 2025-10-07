from django.urls import path
from .views import GoogleSheetListView, GoogleSheetDataView

urlpatterns = [
    path("google-sheets/", GoogleSheetListView.as_view(), name="google-sheet-list"),
    path("google-sheets/<int:sheet_id>/data/", GoogleSheetDataView.as_view(), name="google-sheet-data"),
]
