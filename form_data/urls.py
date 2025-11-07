from django.urls import path
from .views import FormDataAPIView  , ScheduleInterviewAPIView
from .cvviews import GenerateCVAPIView

urlpatterns = [
    path('formdata/', FormDataAPIView.as_view(), name='formdata'),
    path('formdata/<int:pk>/', FormDataAPIView.as_view(), name='formdata-detail'),
    path('schedule-interview/', ScheduleInterviewAPIView.as_view(), name='schedule-interview'),
    path("formdata/<int:pk>/generate-cv/", GenerateCVAPIView.as_view(), name="generate-cv"),
]
