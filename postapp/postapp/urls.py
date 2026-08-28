"""
Main URL configuration for PostKnob.
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from postknob import views

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Landing & static pages
    path("", views.home, name="home"),

    # App views
    path("postknob/", include("postknob.urls")),

    # Django auth (login, logout, password reset…)
    path("accounts/", include("django.contrib.auth.urls")),

    # REST API v1
    path("api/v1/", include("postknob.api.urls")),

    # JWT token endpoints
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),

    # OpenAPI / Swagger
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # Health check (also available at /api/v1/health/ via API router)
    path("health/", views.health_check, name="health_check"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
