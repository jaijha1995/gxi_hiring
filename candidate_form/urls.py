# candidate_form/urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path, include
# from .views import ApplicationFormViewSet, ApplicationStatusHistoryViewSet
# candidate_form/urls.py
from .views import (
    ApplicationFormAPIView,
    ChangePhaseAPIView,
    RollbackAPIView,
    MyCandidatesAPIView,
)

urlpatterns = [
    # CRUD endpoints
    path('applications/', ApplicationFormAPIView.as_view(), name='applications-list-create'),        # GET list, POST create
    path('applications/<int:pk>/', ApplicationFormAPIView.as_view(), name='applications-detail'),    # GET single, PUT, PATCH, DELETE

    # Custom actions
    path('applications/<int:pk>/change-phase/', ChangePhaseAPIView.as_view(), name='applications-change-phase'),
    path('applications/<int:pk>/rollback/', RollbackAPIView.as_view(), name='applications-rollback'),
    # for logged-in user's candidates
    path('applications/my-candidates/', MyCandidatesAPIView.as_view(), name='my-candidates'),

    # for superuser/staff to query a specific HR's candidates
    path('applications/<int:hr_id>/my-candidates/', MyCandidatesAPIView.as_view(), name='hr-my-candidates'),

]

