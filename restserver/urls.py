from django.contrib import admin
from django.urls import path , include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/superadmin/', include('superadmin.urls')),
    path('api/google_sheet/', include('google_sheet.urls')),
    path('api/profile_details/', include('profile_details.urls')),
    path('api/google_form_work/', include('google_form_work.urls')),
    path('api/candidates/', include('candidate_form.urls')),
]
