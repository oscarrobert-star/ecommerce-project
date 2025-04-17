from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Order
from .serializers import OrderSerializer
import logging

logger = logging.getLogger("order_service")


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by("-created_at")
    serializer_class = OrderSerializer

    def list(self, request):
        logger.info("GET /orders - Fetching all orders")
        return super().list(request)

    def retrieve(self, request, *args, **kwargs):
        logger.info(f"GET /orders/{kwargs.get('pk')} - Fetching order details")
        return super().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        logger.info("POST /orders - Creating new order")
        response = super().create(request, *args, **kwargs)
        logger.info(f"Order created with ID: {response.data.get('id')}")
        return response

    def update_payment_status(self, request, pk=None):
        logger.info(f"PATCH /orders/{pk}/payment_status - Updating payment status")
        order = self.get_object()
        status_value = request.data.get("payment_status")
        if status_value in dict(Order._meta.get_field('payment_status').choices):
            order.payment_status = status_value
            order.save()
            logger.info(f"Payment status updated to '{status_value}' for order {order.id}")
            return Response({"status": "payment status updated"})
        logger.error(f"Invalid payment status '{status_value}' for order {order.id}")
        return Response({"error": "Invalid status"}, status=400)

    def update_shipping_status(self, request, pk=None):
        logger.info(f"PATCH /orders/{pk}/shipping_status - Updating shipping status")
        order = self.get_object()
        status_value = request.data.get("shipping_status")
        if status_value in dict(Order._meta.get_field('shipping_status').choices):
            order.shipping_status = status_value
            order.save()
            logger.info(f"Shipping status updated to '{status_value}' for order {order.id}")
            return Response({"status": "shipping status updated"})
        logger.error(f"Invalid shipping status '{status_value}' for order {order.id}")
        return Response({"error": "Invalid status"}, status=400)

