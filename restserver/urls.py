from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/superadmin/', include('superadmin.urls')),
    path('summernote/', include('django_summernote.urls')),
    path('api/google_sheet/', include('google_sheet.urls')),
    path('api/profile_details/', include('profile_details.urls')),
    path('api/google_form_work/', include('google_form_work.urls')),
    path('api/candidates/', include('candidate_form.urls')),
    path('api/form_data/', include('form_data.urls')),
    path('api/create_job/', include('create_job.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
