"""
URL configuration for EduTrack project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [

    path("favicon.ico", RedirectView.as_view(url="/static/favicon.ico", permanent=False), name="favicon"),

    path("admin/", admin.site.urls),

    path("", include("apps.public.urls")),

    path("dashboard/", include(("apps.dashboard.urls", "dashboard"), namespace="dashboard")),

    path("students/", include("apps.students.urls")),

    path("faculty/", include("apps.faculty.urls")),

    path("api/faculty/", include("apps.faculty.api_urls")),

    path("Institute/", include(("apps.institute_app.urls" , "institute") , namespace="institute")),

    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
