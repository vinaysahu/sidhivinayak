"""
URL configuration for sidhivinayak project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from projects.views import get_worker_wages
from customers.views import customer_login, customer_logout, customer_dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path('customer/', customer_login, name='customer'),
    path('customer/login/', customer_login, name='login'),
    path('customer/logout/', customer_logout, name='logout'),
    path('customer/profile/', customer_dashboard, name='profile'),
    path('customer/dashboard/', customer_dashboard, name='dashboard'),
    path("projects/get-worker-wages/", get_worker_wages, name="get-worker-wages"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

