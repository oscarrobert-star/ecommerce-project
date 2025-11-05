import requests
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
import hashlib
import hmac
import logging # 🌟 ADDED: Import logging module

# Configure logger for this module
logger = logging.getLogger(__name__)

PAYSTACK_SECRET = os.getenv("PAYSTACK_SECRET_KEY")
CALLBACK_URL = os.getenv("CALLBACK_URL")  # your e-commerce callback

@csrf_exempt
def pay(request):
    """
    Initializes a new payment transaction with Paystack.
    """
    if request.method != "POST":
        return HttpResponse(status=405)
        
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        logger.error("Paystack initialization failed: Invalid JSON payload received.")
        return JsonResponse({"error": "Invalid JSON"}, status=400)
        
    email = data.get("email")
    amount = data.get("amount")  
    channel = data.get("channel", "card") # Default to card if not specified
    order_id = data.get("order_id")
    
    # Validate input
    if not email or not amount:
        logger.error("Paystack initialization failed: Email and amount are required.")
        return JsonResponse({"error": "Email and amount are required."}, status=400)

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET}",
        "Content-Type": "application/json",
    }
    
    # Ensure amount is an integer (required by Paystack)
    try:
        amount_kobo = int(amount) * 100
    except ValueError:
        logger.error(f"Paystack initialization failed: Invalid amount value '{amount}'.")
        return JsonResponse({"error": "Invalid amount value."}, status=400)
    
    payload = {
        "email": email,
        "amount": amount_kobo,
        "callback_url": f"{os.environ.get('PAYMENT_CALLBACK')}/order-confirmation?order={order_id}",
        "channels": [channel],
        "currency": "KES",
        "metadata": {
            "order_id": order_id,
        }
    }
    
    logger.info(f"Initializing Paystack transaction for order: {order_id}, amount: {amount}")

    try:
        response = requests.post("https://api.paystack.co/transaction/initialize", json=payload, headers=headers)
        response.raise_for_status()
        logger.info(f"Paystack initialization successful for order {order_id}. Status: {response.status_code}")
        return JsonResponse(response.json(), status=response.status_code)
    except requests.exceptions.RequestException as e:
        logger.critical(f"Paystack API request failed for order {order_id}: {str(e)}", exc_info=True)
        return JsonResponse({"error": "Payment initialization failed via external API."}, status=500)

@csrf_exempt
def webhook(request):
    """
    Handles POST requests from Paystack webhooks to confirm payment status.
    """
    if request.method != "POST":
        return HttpResponse(status=405)
        
    # --- 1. Verify the signature ---
    received_signature = request.headers.get("x-paystack-signature")
    
    if not received_signature:
        logger.warning("Webhook received but signature header is missing.")
        return JsonResponse({"error": "Missing signature"}, status=400)
    
    if not verify_signature(request.body, received_signature, PAYSTACK_SECRET):
        logger.critical("SECURITY ALERT: Webhook received with invalid signature.")
        return JsonResponse({"error": "Invalid signature"}, status=400)
    
    # --- 2. Process Data ---
    try:
        data = json.loads(request.body)
        event = data.get("event")
    except json.JSONDecodeError:
        logger.error("Webhook received with invalid JSON body.")
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    logger.info(f"Webhook received, Event: {event}")
    
    if event == "charge.success":
        reference = data["data"]["reference"]
        order_id = data["data"]["metadata"].get("order_id")
        
        logger.info(f"Payment success event for reference: {reference}, Order ID: {order_id}")

        if order_id:
            # --- 3. FIX: Correct API Endpoint Call ---
            try:
                ORDERS_SERVICE_URL = os.getenv("ORDERS_SERVICE_URL")
                
                # The 404 error shows the Orders Service expects: 
                # PATCH /orders/{pk}/payment_status 
                # (OR /orders/{pk}/payment_status/ if trailing slash is required)
                
                payload = {
                    "payment_status": "paid",
                    "payment_reference": reference,
                }
                headers = {"Content-Type": "application/json"}
                
                # 🌟 FIXED URL: Changed from /update-payment-status/ (which produced 404) 
                # to the correct endpoint pattern /payment_status/
                resp = requests.patch( # Use PATCH as defined in OrderViewSet
                    f"{ORDERS_SERVICE_URL}/orders/{order_id}/payment_status",
                    json=payload,
                    headers=headers,
                    timeout=5,
                )
                
                if resp.status_code == 200:
                    logger.info(f"Order status updated successfully for order {order_id}.")
                else:
                    logger.error(f"Failed to update order status for order {order_id}. Status: {resp.status_code}. Response: {resp.text}")

            except requests.exceptions.RequestException as e:
                logger.critical(f"Connection error updating order status for {order_id}: {str(e)}", exc_info=True)
            except Exception as e:
                logger.critical(f"Unexpected error during order status update: {str(e)}", exc_info=True)
        else:
            logger.warning(f"Payment successful but Order ID not found in metadata for reference: {reference}.")
    
    # Paystack requires a 200 OK status regardless of processing success/failure
    return HttpResponse(status=200)


def verify_signature(request_body, received_signature, secret_key):
    """
    Computes HMAC signature and compares it with the received signature.
    """
    computed = hmac.new(
        secret_key.encode(),
        msg=request_body,
        digestmod=hashlib.sha512
    ).hexdigest()
    return hmac.compare_digest(computed, received_signature)


def health_check(request):
    """
    Health check endpoint to verify if the service is running.
    """
    return JsonResponse({"status": "ok"}, status=200)