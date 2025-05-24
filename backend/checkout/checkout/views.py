import json
import logging
import requests
from .services import order_service
from .services import payment_service
from django.http import JsonResponse,  HttpResponse
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

'''
POST /checkout
{
    "email": "",
    "amount": 5000,
    "channel": "card",
    "items": [
        {
        "product_id": "prod001",
        "product_name": "Cool Widget",
        "quantity": 2,
        "price": "19.99"
        },
        {
        "product_id": "prod002",
        "product_name": "Hot Gadget",
        "quantity": 1,
        "price": "49.99"
        }
    ]
}
'''
@csrf_exempt
def checkout(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email = data.get("email")
        amount = data.get("amount")
        channel = data.get("channel")  
        items = data.get("items") 
        # Validate input
        if not email or not amount:
            return JsonResponse({"error": "Email and amount are required."}, status=400)

        # Create order
        logging.info("Calling oerder service to create order")
        order = order_service.create_order(email=email,items=items)

        if not order:
            return JsonResponse({"error": "Failed to create order."}, status=500)
        
        order_id = order.get("id")

        # Initialize payment
        payment_response = payment_service.initialize_payment(email=email, amount=amount, channel=channel, order_id=order_id)

        if not isinstance(payment_response, dict):
            logging.error("Invalid payment response format")
            return JsonResponse({"error": "Failed to initialize payment"}, status=500)

        return JsonResponse(payment_response)