from django.urls import include, path

urlpatterns = [
    path("api/", include("api.urls")),
    path("health/", include("api.health_urls")),
]
