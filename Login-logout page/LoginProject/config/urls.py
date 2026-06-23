from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib import admin
from django.shortcuts import redirect


def redirect_admin(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')
    return redirect('login')


urlpatterns = [
    path('django-admin/', admin.site.urls),  # raw Django admin moved here
    path('admin/', redirect_admin),           # /admin/ now goes to custom dashboard
    path('', include('accounts.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)