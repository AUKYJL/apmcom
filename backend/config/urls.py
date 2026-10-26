from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = 'Лесная Чашка — админка акции'
admin.site.site_title = 'Лесная Чашка'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('promo.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
