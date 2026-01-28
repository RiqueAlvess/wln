from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('apps.accounts.urls')),
    path('dashboard/', include('apps.analytics.urls')),
    path('campaigns/', include('apps.surveys.urls')),
    path('invitations/', include('apps.invitations.urls')),
    path('survey/', include('apps.responses.urls')),
    path('actions/', include('apps.actions.urls')),
    path('', include('apps.core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers
handler400 = 'config.error_handlers.handler400'
handler403 = 'config.error_handlers.handler403'
handler404 = 'config.error_handlers.handler404'
handler500 = 'config.error_handlers.handler500'
