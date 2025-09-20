from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet

router = DefaultRouter(trailing_slash=False)
router.register("notifications", NotificationViewSet, basename="notifications")

urlpatterns = [
    # DRF router handles:
    #   GET    /notifications       -> list (paginated)
    #   GET    /notifications/<id>  -> retrieve
    #   POST   /notifications       -> create (if needed)
    path("", include(router.urls)),

    # Custom actions
    path("notifications/send", NotificationViewSet.as_view({"post": "send"}), name="send-notification"),
    path("notifications/health", NotificationViewSet.health_check, name="health_check"),
]
