from django.urls import path
from .views import GoogleSheetAPIView, GoogleFormResponsesAPIView
from .allviews import GoogleFormAllSheetsAPIView

urlpatterns = [
    path('sheets/', GoogleSheetAPIView.as_view(), name='sheets-list-create'),
    path('sheets/<str:sheet_id>/', GoogleFormResponsesAPIView.as_view(), name='google-form-responses'),
    path("google_forms/", GoogleFormAllSheetsAPIView.as_view(), name="google_form_all_sheets"),
]
