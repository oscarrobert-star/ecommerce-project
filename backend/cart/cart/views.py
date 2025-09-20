# from django.http import JsonResponse
# from django.views.decorators.http import require_http_methods
# from django.views.decorators.csrf import csrf_exempt
# import json

# from .utils import get_cart, add_to_cart, remove_from_cart, clear_cart

# @csrf_exempt
# @require_http_methods(["GET"])
# def view_cart(request, user_id):
#     return JsonResponse({"cart": get_cart(user_id)})

# @csrf_exempt
# @require_http_methods(["POST"])
# def add_item(request, user_id):
#     item = json.loads(request.body)
#     add_to_cart(user_id, item)
#     return JsonResponse({"message": "Item added"})

# @csrf_exempt
# @require_http_methods(["DELETE"])
# def remove_item(request, user_id, product_id):
#     remove_from_cart(user_id, product_id)
#     return JsonResponse({"message": "Item removed"})

# @csrf_exempt
# @require_http_methods(["DELETE"])
# def clear(request, user_id):
#     clear_cart(user_id)
#     return JsonResponse({"message": "Cart cleared"})
# ---------------------------------------------------------------------
import redis
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .utils import get_cart_id
import logging

# Redis client
redis_client = redis.StrictRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    decode_responses=True
)

@csrf_exempt
def add_to_cart(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        cart_id = get_cart_id(request)
        data = json.loads(request.body)
        product_id = str(data.get('product_id'))
        quantity = int(data.get('quantity', 1))
        product_name = str(data.get('product_name'))
        price = str(data.get('price'))

        redis_key = f"cart:{cart_id}"
        # If the product already exists, update quantity
        existing_item = redis_client.hget(redis_key, product_id)
        if existing_item:
            existing_item_data = json.loads(existing_item)
            quantity += int(existing_item_data.get('quantity', 0))

        item_data = {
            "product_id": product_id,
            "product_name": product_name,
            "quantity": quantity,
            "price": price,
        }

        redis_client.hset(redis_key, product_id, json.dumps(item_data))
        redis_client.expire(redis_key, getattr(settings, "CART_TTL_SECONDS", 300))

        logging.info(f"Item {product_id} added to cart {cart_id} with quantity {quantity}")
        return JsonResponse({'message': 'Item added', 'cart_id': cart_id})

    except Exception as e:
        logging.exception("Failed to add item to cart")
        return JsonResponse({'error': str(e)}, status=500)


def get_cart(request):
    cart_id = get_cart_id(request)
    redis_key = f"cart:{cart_id}"
    raw_items = redis_client.hgetall(redis_key)

    if not raw_items:
        return JsonResponse({'message': 'Cart is empty'}, status=404)

    items = []
    for item_json in raw_items.values():
        try:
            items.append(json.loads(item_json))
        except Exception:
            continue

    logging.info(f"Cart {cart_id} retrieved with items: {items}")
    return JsonResponse({'cart_id': cart_id, 'items': items})


@csrf_exempt
def remove_from_cart(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        cart_id = get_cart_id(request)
        data = json.loads(request.body)
        product_id = str(data.get('product_id'))

        redis_key = f"cart:{cart_id}"
        redis_client.hdel(redis_key, product_id)
        logging.info(f"Item {product_id} removed from cart {cart_id}")
        return JsonResponse({'message': 'Item removed', 'cart_id': cart_id})
    except Exception as e:
        logging.exception("Failed to remove item from cart")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def clear_cart(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        cart_id = get_cart_id(request)
        redis_key = f"cart:{cart_id}"
        redis_client.delete(redis_key)
        logging.info(f"Cart {cart_id} cleared")
        return JsonResponse({'message': 'Cart cleared', 'cart_id': cart_id})
    except Exception as e:
        logging.exception("Failed to clear cart")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def edit_item_quantity(request):
    if request.method != 'PATCH':
        return JsonResponse({'error': 'Only PATCH allowed'}, status=405)

    try:
        cart_id = get_cart_id(request)
        data = json.loads(request.body)
        product_id = str(data.get('product_id'))
        quantity = int(data.get('quantity', 1))

        redis_key = f"cart:{cart_id}"
        item_json = redis_client.hget(redis_key, product_id)

        if not item_json:
            return JsonResponse({'error': 'Item not found in cart'}, status=404)

        if quantity <= 0:
            redis_client.hdel(redis_key, product_id)
            logging.info(f"Item {product_id} removed from cart {cart_id} due to non-positive quantity")
            return JsonResponse({'message': 'Item removed due to non-positive quantity', 'cart_id': cart_id})

        item = json.loads(item_json)
        item['quantity'] = quantity

        redis_client.hset(redis_key, product_id, json.dumps(item))
        redis_client.expire(redis_key, getattr(settings, "CART_TTL_SECONDS", 300))
        logging.info(f"Item {product_id} quantity updated to {quantity} in cart {cart_id}")
        return JsonResponse({'message': 'Item quantity updated', 'cart_id': cart_id})
    except Exception as e:
        logging.exception("Failed to update item quantity")
        return JsonResponse({'error': str(e)}, status=500)

def health_check(request):
    try:
        # Try pinging Redis
        logging.info("Checking Redis health")
        if not redis_client.ping():
            logging.error("Redis is not reachable")
            raise Exception("Redis is not reachable")
        # redis_client.ping()
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        logging.exception(f"Health check failed with error {e}")
        return JsonResponse({'status': 'error', 'details': str(e)}, status=500)

def get_cart_ttl(request):
    """
    Returns the remaining time-to-live for the current cart.
    """
    try:
        cart_id = get_cart_id(request)
        redis_key = f"cart:{cart_id}"
        ttl = redis_client.ttl(redis_key)
        
        # Redis returns -1 if the key exists but has no associated expire.
        # It returns -2 if the key does not exist.
        if ttl < 0:
            ttl = 0
            
        logging.info(f"TTL for cart {cart_id} is {ttl} seconds.")
        return JsonResponse({'ttl': ttl})
    except Exception as e:
        logging.exception("Failed to get cart TTL")
        return JsonResponse({'error': str(e)}, status=500)        