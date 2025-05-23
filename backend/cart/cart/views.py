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
# def remove_item(request, user_id, item_id):
#     remove_from_cart(user_id, item_id)
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

    cart_id = get_cart_id(request)
    data = json.loads(request.body)
    item_id = str(data.get('item_id'))
    quantity = int(data.get('quantity', 1))

    redis_key = f"cart:{cart_id}"
    redis_client.hincrby(redis_key, item_id, quantity)
    redis_client.expire(redis_key, getattr(settings, "CART_TTL_SECONDS", 300))
    logging.info(f"Item {item_id} added to cart {cart_id} with quantity {quantity}")
    return JsonResponse({'message': 'Item added', 'cart_id': cart_id})

def get_cart(request):
    cart_id = get_cart_id(request)
    redis_key = f"cart:{cart_id}"
    items = redis_client.hgetall(redis_key)
    logging.info(f"Cart {cart_id} retrieved with items: {items}")
    if not items:
        return JsonResponse({'message': 'Cart is empty'}, status=404)
    return JsonResponse({'cart_id': cart_id, 'items': items})

@csrf_exempt
def remove_from_cart(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    cart_id = get_cart_id(request)
    data = json.loads(request.body)
    item_id = str(data.get('item_id'))

    redis_key = f"cart:{cart_id}"
    redis_client.hdel(redis_key, item_id)
    logging.info(f"Item {item_id} removed from cart {cart_id}")
    return JsonResponse({'message': 'Item removed', 'cart_id': cart_id})

@csrf_exempt
def clear_cart(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    cart_id = get_cart_id(request)
    redis_key = f"cart:{cart_id}"
    redis_client.delete(redis_key)
    logging.info(f"Cart {cart_id} cleared")
    return JsonResponse({'message': 'Cart cleared', 'cart_id': cart_id})

@csrf_exempt
def edit_item_quantity(request):
    if request.method != 'PATCH':
        return JsonResponse({'error': 'Only PATCH allowed'}, status=405)

    cart_id = get_cart_id(request)
    data = json.loads(request.body)
    item_id = str(data.get('item_id'))
    quantity = int(data.get('quantity', 1))

    redis_key = f"cart:{cart_id}"

    if quantity <= 0:
        redis_client.hdel(redis_key, item_id)
        logging.info(f"Item {item_id} removed from cart {cart_id} due to non-positive quantity")
        return JsonResponse({'message': 'Item removed due to non-positive quantity', 'cart_id': cart_id})

    redis_client.hset(redis_key, item_id, quantity)
    redis_client.expire(redis_key, getattr(settings, "CART_TTL_SECONDS", 300))
    logging.info(f"Item {item_id} quantity updated to {quantity} in cart {cart_id}")
    return JsonResponse({'message': 'Item quantity updated', 'cart_id': cart_id})
