from django.urls import path
from .views import UpdateTaskStatusAPIView

urlpatterns = [
    path("tasks/", UpdateTaskStatusAPIView.as_view(), name="task-list"),             # GET all
    path("tasks/<int:pk>/", UpdateTaskStatusAPIView.as_view(), name="task-detail"),  # GET one
    path("tasks/<int:pk>/update/", UpdateTaskStatusAPIView.as_view(), name="task-update"),  # PUT
]
