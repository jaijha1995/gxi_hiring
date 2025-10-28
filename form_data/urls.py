from django.urls import path
from .views import FormDataAPIView

urlpatterns = [
    path('formdata/', FormDataAPIView.as_view(), name='formdata'),
    path('formdata/<int:pk>/', FormDataAPIView.as_view(), name='formdata-detail'),
]
