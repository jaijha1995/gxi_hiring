from rest_framework.urlpatterns import path
from .views import googleAPIView , GoogleFormResponsesView

urlpatterns = [
    path('googleform/', googleAPIView.as_view(), name='address-list'),
    path('googleform/responses/', GoogleFormResponsesView.as_view(), name='googleform-responses'),
   ]