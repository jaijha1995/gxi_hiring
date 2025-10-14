from django.urls import path
from .views import CandidateDetailsAPIView, CandidateStatusHistoryAPIView , ShiftCandidateStatusView
from .profileviews import CandidateDetailsView , CandidateListView

urlpatterns = [
    path('candidates/', CandidateDetailsAPIView.as_view()),                # GET all, POST create
    path('candidates/<str:pk>/', CandidateDetailsAPIView.as_view()),       # GET one, PATCH update, DELETE delete
    path('candidates/<int:candidate_id>/history/', CandidateStatusHistoryAPIView.as_view()),  # GET history
    path('shift-status/', ShiftCandidateStatusView.as_view(), name='shift-status'),
    path('profile_status/', CandidateDetailsView.as_view(), name='profile-shift-status'),  # New URL pattern
    path("listcandidates/", CandidateListView.as_view(), name="list-candidates"),  # New URL pattern
]