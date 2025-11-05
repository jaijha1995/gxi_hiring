# app/urls.py
from django.urls import path
from .views import (
    CustomerViews, LoginCustomer, CustomerManageViews,
    OTPView, VerifyOTP, ForgotPasswordAPIView , ManagerTeamListAPIView
)

urlpatterns = [
    path('signup/', CustomerViews.as_view(), name='signup'),
    path('login/', LoginCustomer.as_view(), name='login'),
    path('users/', CustomerManageViews.as_view(), name='users-list'),
    path('users/<int:id>/', CustomerManageViews.as_view(), name='users-detail'),
    path('send-otp/', OTPView.as_view(), name='send-otp'),
    path('verify-otp/', VerifyOTP.as_view(), name='verify-otp'),
    path('forgot-password/', ForgotPasswordAPIView.as_view(), name='forgot-password'),
    path('manager_list/', ManagerTeamListAPIView.as_view(), name='manager-list'),
]
