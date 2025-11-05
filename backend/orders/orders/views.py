# order_service/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Order
from .serializers import OrderSerializer
import logging
from django.http import JsonResponse
from rest_framework.decorators import action, api_view
from django.db import connections, transaction
from django.db.utils import OperationalError
from django.conf import settings 
import requests 

logger = logging.getLogger("order_service")

# --- Cross-Service Communication Configuration ---
PRODUCT_SERVICE_URL = getattr(settings, "PRODUCT_SERVICE_URL", "http://product-service:8000/products") 

def call_product_service_stock_update(items_data, transaction_type):
    """Makes an HTTP call to the Product Service's update_stock endpoint."""
    payload = {
        "items": items_data,
        "transaction_type": transaction_type
    }
    
    try:
        response = requests.patch(
            f"{PRODUCT_SERVICE_URL}/update_stock", 
            json=payload,
            timeout=5 
        )
        response.raise_for_status() # Raises an HTTPError for 4xx or 5xx responses
        return True, response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to communicate with Product Service for {transaction_type}: {e}")
        if hasattr(e, 'response') and e.response is not None:
             logger.error(f"Product Service Response: {e.response.text}")
             try:
                 return False, e.response.json()
             except json.JSONDecodeError:
                 return False, {"error": "Product Service error and invalid JSON response."}
        return False, {"error": "Product Service communication failure."}

def health_check(request):
    # logging.info("Health check initiated")
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

    @transaction.atomic 
    def create(self, request, *args, **kwargs):
        logger.info("POST /orders - Creating new order (Stock reservation assumed via Cart Service)")
        
        # 1. Validate Order
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 2. Create the Order
        # We assume the items in the request came from a cart that successfully 
        # used DECRBY on the Redis stock counter, so we proceed directly.
        self.perform_create(serializer)
        order_id = serializer.instance.id
        logger.info(f"Order created with ID: {order_id}.")
        
        # NOTE: A robust system would also call the Cart Service here to DELETE the cart
        # and prevent the 30-minute cart TTL from releasing the stock reservation!
        
        
        return Response({"id": order_id}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"], url_path="payment_status")
    def update_payment_status(self, request, pk=None):
        logger.info(f"PATCH /orders/{pk}/payment_status - Updating payment status")
        
        order = self.get_object()
        old_status = order.payment_status
        status_value = request.data.get("payment_status")
        payment_ref = request.data.get("payment_reference")

        valid_statuses = dict(Order._meta.get_field('payment_status').choices)

        if status_value not in valid_statuses:
            return Response({"error": "Invalid status"}, status=400)

        # 1. Stock Commit/Release Logic (only if status is changing)
        if old_status != status_value and (status_value == 'paid' or status_value == 'failed'):
            
            items_data = [{'product_id': item.product_id, 'quantity': item.quantity} for item in order.items.all()]

            if status_value == 'paid':
                # Payment success: COMMIT the reservation (Reduce actual DB stock)
                logger.info(f"Payment successful for order {order.id}. Committing final stock...")
                success, response_data = call_product_service_stock_update(items_data, 'COMMIT')
                if not success:
                    logger.critical(f"CRITICAL: Stock commit failed after payment for order {order.id}! {response_data}")

            elif status_value == 'failed':
                # Payment failure: RELEASE the reservation (Make stock available again in DB as safety)
                logger.info(f"Payment failed for order {order.id}. Releasing stock (safety rollback)...")
                # NOTE: In a pure Redis system, the Cart TTL should handle the release. 
                # This call serves as a safety/cleanup in case the TTL worker fails or is slow.
                success, response_data = call_product_service_stock_update(items_data, 'RELEASE')
                if not success:
                    logger.critical(f"CRITICAL: Stock release failed after payment failed for order {order.id}! {response_data}")

        # 2. Update and Save Order Status
        order.payment_status = status_value
        if payment_ref:
            order.payment_reference = payment_ref
        
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