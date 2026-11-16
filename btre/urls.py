from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static 
from django.views.static import serve


urlpatterns = [
    path('',include('pages.urls')),
    path('listings/',include('listings.urls')),
    path('accounts/',include('accounts.urls')),
    path('contacts/',include('contacts.urls')),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Demo deployment without a file-storage service: let Django serve the
    # (small) media folder. A real production site would use S3/Cloudinary.
    urlpatterns += [re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT})]


