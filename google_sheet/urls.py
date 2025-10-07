from django.urls import path
from .views import hiringprocessListView, HiringSheetDataView

urlpatterns = [
    path("hiring/", hiringprocessListView.as_view(), name="google-sheet-list"),
    path("hiring/<int:integration_id>/data/", HiringSheetDataView.as_view(), name="google-sheet-data"),
]
