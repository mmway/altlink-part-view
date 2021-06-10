"""alter_link_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from django.urls.conf import re_path

# teraz zrobić reetowanie hasła  https://learndjango.com/tutorials/django-password-reset-tutorial
urlpatterns = [
    path('', include('altlink.urls')),
    path('admin/', admin.site.urls, name='login-admin'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/', include('useralter.urls')),
    # path('alt-article/create/', admin.site.urls, name='logines'),
    path('nested_admin/', include('nested_admin.urls')),
    # path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    re_path(r'^i18n/', include('django.conf.urls.i18n')),
    
    # 3rd party app - Adding social auth path
    path('social-auth/', include('social_django.urls', namespace="social")),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)