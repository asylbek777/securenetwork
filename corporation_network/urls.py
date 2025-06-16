"""
URL configuration for corporation_network project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path
from main.views import custom_login, logout_view, register_view, home, chat, upload_assignment, schedule, \
    assignment_detail, news, setup_otp, verify_otp, custom_login
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from main.views import ChatBotView
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', custom_login, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    path('home/', home, name='home'),
    path('chat/', chat, name='chat'),
    path('upload_assignment/', upload_assignment, name='upload_assignment'),
    path('schedule/', schedule, name='schedule'),
    path('assignment/<int:assignment_id>/', assignment_detail, name='assignment_detail'),
    path('news/', news, name='news'),
    path('chatbot/', ChatBotView.as_view(), name='chatbot_api'),
    path('setup_otp/', setup_otp, name='setup_otp'),
    path('verify_otp/', verify_otp, name='verify_otp'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
