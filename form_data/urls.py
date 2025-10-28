from django.urls import path
from .views import FormDataAPIView

urlpatterns = [
    path('formdata/', FormDataAPIView.as_view(), name='formdata'),
]
