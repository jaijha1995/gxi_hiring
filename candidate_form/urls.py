# candidate_form/urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import ApplicationFormViewSet, ApplicationStatusHistoryViewSet

router = DefaultRouter()
router.register(r"applications", ApplicationFormViewSet, basename="application")
router.register(r"application-actions", ApplicationStatusHistoryViewSet, basename="application-action")

urlpatterns = [
    path("", include(router.urls)),
]
