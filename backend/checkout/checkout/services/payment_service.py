'''
to initialize the payment we need:
{
  "email": "customer@example.com",
  "amount": 5000,
  "channel": "card",
  "order_id" : "ord_312"
}
email - from /checkout endpoint
amount - from /checkout endpoint (total of all items)
channel - from /checkout endpoint 
order_id - from crete order endpoint 
'''
import os
import json
import logging
import requests
from django.conf import settings
from django.http import JsonResponse, HttpResponse

PAYMENT_SERVICE_URL = os.environ.get("PAYMENT_SERVICE_URL")
url = f"{PAYMENT_SERVICE_URL}/payments/pay"
# url = "http://localhost:8005/payments/pay/"  # Replace with your actual payment service URL

def initialize_payment(email, amount, channel, order_id):
    logging.info(f"Request received to initialize payment for email: {email}")
    payment_data = {
        "email": email,
        "amount": amount,
        "channel": channel,
        "order_id": order_id
    }
    try:
        response = requests.post(url, json=payment_data)
        if response.status_code == 200:
            logging.info(f"Payment initialized successfully: {response.json()}")
            return response.json()
        else:
            logging.error(f"Failed to initialize payment: {response.status_code} - {response.text}")
            return JsonResponse({"error": "Failed to initialize payment"}, status=response.status_code)
    except requests.RequestException as e:
        logging.error(f"Request failed: {e}")
        return JsonResponse({"error": "Request failed"}, status=500)
    
    