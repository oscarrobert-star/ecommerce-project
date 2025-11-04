import requests
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
import hashlib
import hmac

PAYSTACK_SECRET = os.getenv("PAYSTACK_SECRET_KEY")
CALLBACK_URL = os.getenv("CALLBACK_URL")  # your e-commerce callback

@csrf_exempt
def pay(request):
    data = json.loads(request.body)
    email = data.get("email")
    amount = data.get("amount")  
    channel = data.get("channel")  # Optional, if you want to specify a payment channel
    order_id = data.get("order_id")  # Optional, if you want to pass order ID
    
    # Validate input
    if not email or not amount:
        return JsonResponse({"error": "Email and amount are required."}, status=400)

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET}",
        "Content-Type": "application/json",
    }
    payload = {
        "email": email,
        "amount": int(amount) * 100,
        "callback_url": f"{os.environ.get('PAYMENT_CALLBACK')}/order-confirmation?order={order_id}",
        "channels": [channel],
        "currency": "KES",
        "metadata": {
            "order_id": order_id,  # Optional, if you want to pass order ID
        }
    }

    response = requests.post("https://api.paystack.co/transaction/initialize", json=payload, headers=headers)
    return JsonResponse(response.json())


@csrf_exempt
# def webhook(request):
#     data = json.loads(request.body)
    
#     if data.get("event") == "charge.success":
#         payment_info = {
#             "status": "success",
#             "reference": data["data"]["reference"],
#             "amount": data["data"]["amount"],
#             "email": data["data"]["customer"]["email"]
#         }

#         # Send callback to e-commerce app
#         try:
#             requests.post(CALLBACK_URL, json=payment_info)
#         except Exception as e:
#             print("Callback failed:", str(e))

#     return HttpResponse(status=200)

def webhook(request):
    # Verify the signature
    received_signature = request.headers.get("x-paystack-signature")
    if not received_signature:
        return JsonResponse({"error": "Missing signature"}, status=400)
    if not verify_signature(request.body, received_signature, PAYSTACK_SECRET):
        return JsonResponse({"error": "Invalid signature"}, status=400)
            
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print(data)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        if data.get("event") == "charge.success":
            reference = data["data"]["reference"]

            order_id = data["data"]["metadata"].get("order_id")
            if order_id:
                try:
                    # Replace ORDERS_SERVICE_URL with your actual orders service endpoint
                    ORDERS_SERVICE_URL = os.getenv("ORDERS_SERVICE_URL")
                    payload = {
                        "payment_status": "paid",
                        "payment_reference": reference,
                    }
                    headers = {"Content-Type": "application/json"}
                    resp = requests.post(
                        f"{ORDERS_SERVICE_URL}/orders/{order_id}/update-payment-status/",
                        json=payload,
                        headers=headers,
                        timeout=5,
                    )
                    if resp.status_code != 200:
                        print(f"Failed to update order status for order {order_id}: {resp.text}")
                except Exception as e:
                    print(f"Error updating order status: {str(e)}")
            else:
                print("Order ID not found in payment metadata.")
            print(f"Payment successful: {reference}")
        
        return HttpResponse(status=200)

    return HttpResponse(status=405)


def verify_signature(request_body, received_signature, secret_key):
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
    print("Health check endpoint called")
    return JsonResponse({"status": "ok"}, status=200)