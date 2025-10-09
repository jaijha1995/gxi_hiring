from django.contrib import admin
from django.urls import path , include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/superadmin/', include('superadmin.urls')),
    path('api/google_sheet/', include('google_sheet.urls')),
    path('api/profile_details/', include('profile_details.urls')),
]
