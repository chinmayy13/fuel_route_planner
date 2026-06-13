# from django.contrib import admin
# from django.urls import path, include

# urlpatterns = [
#     path("admin/", admin.site.urls),
#     path("api/", include("route_planner.urls")),
# ]

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def welcome(request):
    return JsonResponse({
        "message": "Welcome to Fuel Route Planner API",
        "usage": {
            "endpoint": "/api/route/",
            "method": "POST",
            "body": {
                "start": "New York, NY",
                "finish": "Los Angeles, CA"
            }
        },
        "docs": "Send a POST request to /api/route/ with start and finish locations"
    })

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("route_planner.urls")),
    path("", welcome),
]