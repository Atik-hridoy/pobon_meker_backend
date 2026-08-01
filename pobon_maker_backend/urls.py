"""
URL configuration for pobon_maker_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

from django.http import HttpResponse

def create_admin(request):
    from django.contrib.auth.models import User
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@admin.com', 'admin123')
        return HttpResponse("<h3>Admin created successfully!</h3><p>Username: <b>admin</b></p><p>Password: <b>admin123</b></p>")
    return HttpResponse("<h3>Admin already exists!</h3><p>Username: <b>admin</b></p><p>Password: <b>admin123</b></p>")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('create-admin/', create_admin),
    path('api/accounts/', include('accounts.urls')),
    path('api/products/', include('products.urls')),
    path('api/admin/', include('admin_settings.urls')),
    path('api/checkout/', include('core.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/activity/', include('user_activity.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
