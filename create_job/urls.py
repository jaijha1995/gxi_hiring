from django.urls import path
from .views import SkillsAPIView, JobAPIView

urlpatterns = [
    path('skills/', SkillsAPIView.as_view()),
    path('skills/<int:pk>/', SkillsAPIView.as_view()),

    path('jobs/', JobAPIView.as_view()),
    path('jobs/<int:pk>/', JobAPIView.as_view()),
]