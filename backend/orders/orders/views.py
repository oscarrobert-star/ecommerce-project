from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Order
from .serializers import OrderSerializer
import logging
from django.http import JsonResponse
from rest_framework.decorators import action, api_view
from django.db import connections
from django.db.utils import OperationalError

logger = logging.getLogger("order_service")


def health_check(request):
    logging.info("Health check initiated")
    databases = ["default", "replica"]  # 'default' = write DB, 'replica' = read DB
    status = {}

    for db in databases:
        try:
            connections[db].cursor()
            status[db] = "ok"
        except OperationalError:
            logger.error(f"{db} database connection failed.")
            status[db] = "unreachable"

    return JsonResponse(status)

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
        order_id = response.data.get('id')
        logger.info(f"Order created with ID: {order_id}")
        return Response({"id": order_id}, status=response.status_code)

    def update_payment_status(self, request, pk=None):
        logger.info(f"PATCH /orders/{pk}/payment_status - Updating payment status")
        order = self.get_object()
        status_value = request.data.get("payment_status")
        payment_ref = request.data.get("payment_reference")

        valid_statuses = dict(Order._meta.get_field('payment_status').choices)

        if status_value not in valid_statuses:
            logger.error(f"Invalid payment status '{status_value}' for order {order.id}")
            return Response({"error": "Invalid status"}, status=400)

        order.payment_status = status_value
        if payment_ref:
            order.payment_reference = payment_ref
            logger.info(f"Payment reference '{payment_ref}' set for order {order.id}")

        order.save()
        logger.info(f"Payment status updated to '{status_value}' for order {order.id}")
        return Response({"status": "payment status updated", "payment_reference": order.payment_reference})


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

    # @action(detail=False, methods=["get"], url_path="status/(?P<reference>[^/.]+)")
    # def order_status_by_reference(self, request, reference=None):
    #     logger.info(f"GET /orders/status/{reference} - Fetching order by payment reference")

    #     max_retries = 3
    #     delay = 2  # seconds

    #     for attempt in range(1, max_retries + 1):
    #         try:
    #             order = Order.objects.get(payment_reference=reference)
    #             serializer = self.get_serializer(order)
    #             logger.info(f"Order {order.id} retrieved on attempt {attempt} for payment reference '{reference}'")
    #             return Response(serializer.data, status=status.HTTP_200_OK)
    #         except Order.DoesNotExist:
    #             logger.warning(f"Attempt {attempt}: Order with payment reference '{reference}' not found")
    #             if attempt < max_retries:
    #                 logger.info(f"Retrying in {delay} seconds...")
    #                 time.sleep(delay)
    #             else:
    #                 logger.error(f"Order with payment reference '{reference}' not found after {max_retries} attempts")
    #                 return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=["get"], url_path="status/(?P<reference>[^/.]+)")
    def order_status_by_reference(self, request, reference=None):
        logger.info(f"GET /orders/status/{reference} - Fetching order by payment reference")

        try:
            order = Order.objects.get(payment_reference=reference)
            serializer = self.get_serializer(order)
            logger.info(f"Order {order.id} retrieved for payment reference '{reference}'")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            logger.error(f"Order with payment reference '{reference}' not found")
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)


# @api_view(["GET"])
# def health_check(request):
#     logging.info("Health check endpoint called")
#     return Response({"status": "ok"}, status=status.HTTP_200_OK)