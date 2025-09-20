from rest_framework import viewsets, status, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError
import logging

from .models import Notification
from .serializers import NotificationSerializer, NotificationListSerializer
from . import services

logger = logging.getLogger("notification_service")


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all().order_by("-created_at")
    serializer_class = NotificationSerializer

    # Enable filtering + ordering
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "channel", "recipient"]  # fields allowed for filtering
    ordering_fields = ["created_at", "sent_at", "status"]  # fields allowed for ordering
    ordering = ["-created_at"]  # default ordering

    def get_serializer_class(self):
        if self.action == "list":
            return NotificationListSerializer
        return NotificationSerializer

    @action(detail=False, methods=["post"])
    def send(self, request):
        logger.info("Received request to send notification", extra={"payload": request.data})

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notification = serializer.save()
        logger.debug("Notification object created", extra={"id": notification.id, "channel": notification.channel})

        # Select channel
        result = {"status": "failed"}
        try:
            if notification.channel == "sms":
                logger.info("Sending SMS", extra={"recipient": notification.recipient})
                result = services.send_sms(notification.recipient, notification.message)
            elif notification.channel == "email":
                logger.info("Sending Email", extra={"recipient": notification.recipient})
                result = services.send_email(
                    notification.recipient,
                    subject="Notification",
                    message=notification.message,
                )
        except Exception as e:
            logger.exception("Error while sending notification", extra={"id": notification.id})
            result = {"status": "failed", "error": str(e)}

        # Update DB with result
        notification.status = result["status"]
        if result.get("status") == "sent":
            notification.sent_at = timezone.now()
            logger.info("Notification sent successfully", extra={"id": notification.id})
        else:
            logger.warning("Notification failed", extra={"id": notification.id, "result": result})
        notification.save()

        response_data = {**NotificationSerializer(notification).data, **result}
        logger.debug("Send response prepared", extra={"id": notification.id, "response": response_data})
        return Response(response_data, status=status.HTTP_200_OK)

    def health_check(request):
        logger.info("Health check initiated")
        databases = ["default", "replica"]  # default = write DB, replica = read DB
        status_report = {}

        for db in databases:
            try:
                connections[db].cursor()
                status_report[db] = "ok"
                logger.debug("DB connection healthy", extra={"db": db})
            except OperationalError:
                logger.error("DB connection failed", extra={"db": db})
                status_report[db] = "unreachable"

        logger.info("Health check completed", extra={"status": status_report})
        return JsonResponse(status_report)
