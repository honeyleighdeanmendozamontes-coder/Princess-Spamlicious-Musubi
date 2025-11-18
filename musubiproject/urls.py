# musubiproject/urls.py
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    # Your custom URLs first
    path('', include('musubiapp.urls')),
    
    # Custom admin dashboard (make sure this comes before the main admin)
    path('myadmin/dashboard/', lambda request: redirect('admin_dashboard') if request.user.is_authenticated else redirect('customer_login'), name='admin_redirect'),
    
    # Django admin (this should come after your custom URLs)
    path('admin/', admin.site.urls),
]