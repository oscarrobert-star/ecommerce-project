'''
to create order we need:
{
  "customer_id": "someone@email.com",
  "payment_status": "pending",
  "shipping_status": "pending",
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
we get email from the request body of /checkout
let's use the email as customer_id
items comes from the cart service
'''
import os
import json
import logging
import requests
# from django.conf import settings
# from django.http import JsonResponse, HttpResponse
ORDERS_SERVICE_URL = os.environ.get("ORDERS_SERVICE_URL")
url = f"{ORDERS_SERVICE_URL}/orders/"
# url = "http://localhost:8002/orders/"  # Replace with your actual orders service URL
# TODO: add service to serive autentication
def create_order(email, items):
    logging.info(f"Request received to create order for email: {email}")
    order_data = {
        "customer_id": email,
        "payment_status": "pending",
        "shipping_status": "pending",
        "items": items
    }
    try:
        response = requests.post(url, json=order_data)
        if response.status_code == 201:
            logging.info(f"Order created successfully: {response.json()}")
            return response.json()
        else:
            logging.error(f"Failed to create order: {response.status_code} - {response.text}")
            # return JsonResponse({"error": "Failed to create order"}, status=response.status_code)
            return None
    except requests.RequestException as e:
        logging.error(f"Request failed: {e}")
        # return JsonResponse({"error": "Request failed"}, status=500)
        return None



if __name__ == "__main__":
    # Example usage
    email = "sample@email.com"
    items = [
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
    response = create_order(email, items)    
    print(response)