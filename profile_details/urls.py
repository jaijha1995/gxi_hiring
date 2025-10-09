from django.urls import path
from .views import CandidateDetailsAPIView, CandidateStatusHistoryAPIView

urlpatterns = [
    path('candidates/', CandidateDetailsAPIView.as_view()),                # GET all, POST create
    path('candidates/<int:pk>/', CandidateDetailsAPIView.as_view()),       # GET one, PATCH update, DELETE delete
    path('candidates/<int:candidate_id>/history/', CandidateStatusHistoryAPIView.as_view()),  # GET history
]