from django.urls import path
from .views import hiringprocessListView, HiringSheetDataView , TypeformListView
from .weebhookviews import TypeformWebhookView, SurveyMonkeyWebhookView

urlpatterns = [
    path("hiring/", hiringprocessListView.as_view(), name="google-sheet-list"),
    path("hiring/<int:integration_id>/data/", HiringSheetDataView.as_view(), name="google-sheet-data"),
    path("webhook/typeform/", TypeformWebhookView.as_view(), name="typeform-webhook"),
    path("webhook/surveymonkey/", SurveyMonkeyWebhookView.as_view(), name="surveymonkey-webhook"),
    path('typeform/', TypeformListView.as_view(), name='typeform-list-all'),
    path('typeform/<int:integration_id>/', TypeformListView.as_view(), name='typeform-list-by-id'),

]
