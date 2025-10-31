from django.urls import path
from .views import SkillsAPIView, JobAPIView
from .departmentviews import DepartmentAPIView
from .jobtypesviews import jobtypesAPIView

urlpatterns = [
    path('skills/', SkillsAPIView.as_view()),
    path('skills/<int:pk>/', SkillsAPIView.as_view()),

    path('jobs/', JobAPIView.as_view()),
    path('jobs/<int:pk>/', JobAPIView.as_view()),

    path('department/', DepartmentAPIView.as_view()),
    path('department/<int:pk>/', DepartmentAPIView.as_view()),


    path('jobtypes/', jobtypesAPIView.as_view()),
    path('jobtypes/<int:pk>/', jobtypesAPIView.as_view()),
]