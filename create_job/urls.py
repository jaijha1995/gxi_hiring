from django.urls import path
from .views import SkillsAPIView, JobAPIView
from .departmentviews import DepartmentAPIView
from .jobtypesviews import jobtypesAPIView
from .locationViews import LocationAPIView
from .teamsviews import teamsAPIView

urlpatterns = [
    path('skills/', SkillsAPIView.as_view()),
    path('skills/<int:pk>/', SkillsAPIView.as_view()),

    path('jobs/', JobAPIView.as_view()),
    path('jobs/<int:pk>/', JobAPIView.as_view()),

    path('department/', DepartmentAPIView.as_view()),
    path('department/<int:pk>/', DepartmentAPIView.as_view()),


    path('jobtypes/', jobtypesAPIView.as_view()),
    path('jobtypes/<int:pk>/', jobtypesAPIView.as_view()),



    path("locations/", LocationAPIView.as_view()),
    path("locations/<int:pk>/", LocationAPIView.as_view()),

    path("teams/", teamsAPIView.as_view()),
    path("teams/<int:pk>/", teamsAPIView.as_view()),
]