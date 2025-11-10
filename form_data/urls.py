from django.urls import path
from .views import FormDataAPIView  , ScheduleInterviewAPIView, SendWhatsappMessageAPIView
# from .cvviews import GenerateCVAPIView

urlpatterns = [
    path('formdata/', FormDataAPIView.as_view(), name='formdata'),
    path('formdata/<int:pk>/', FormDataAPIView.as_view(), name='formdata-detail'),
    path('schedule-interview/', ScheduleInterviewAPIView.as_view(), name='schedule-interview'),
    path('send-whatsapp/<int:form_id>/', SendWhatsappMessageAPIView.as_view(), name='send_whatsapp'),
    path("send-whatsapp/", SendWhatsappMessageAPIView.as_view(), name="get_whatsapp_messages"),
    # path("formdata/<int:pk>/generate-cv/", GenerateCVAPIView.as_view(), name="generate-cv"),
]
