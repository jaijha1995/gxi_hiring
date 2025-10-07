from django.urls import path, include
from .views import CustomerViews, ListCustomerViews,LoginCustomer  , OTPView ,VerifyOTP ,ForgotPasswordAPIView

from rest_framework.routers import DefaultRouter


urlpatterns = [
    path('signup/', CustomerViews.as_view()),
    path('signup/<int:id>', CustomerViews.as_view()),
    path('org_id/''<int:org_id>', ListCustomerViews.as_view()),
    path('login/', LoginCustomer.as_view()),
    path('otp/', OTPView.as_view()),
    path('verifyotp/', VerifyOTP.as_view()),
    path('resetpassword/', ForgotPasswordAPIView.as_view()),
]
