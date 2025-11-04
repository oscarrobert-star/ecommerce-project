# cart/views.py
import redis
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .utils import get_cart_id
import logging

logger = logging.getLogger(__name__)

# Redis client
redis_client = redis.StrictRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    decode_responses=True
)

CART_TTL_SECONDS = getattr(settings, "CART_TTL_SECONDS", 900)  # Default to 15 minutes

@csrf_exempt
def add_to_cart(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        # 1. Input/Key Setup
        cart_id = get_cart_id(request)
        data = json.loads(request.body)
        product_id = str(data.get('product_id'))
        requested_quantity = int(data.get('quantity', 1))
        
        cart_key = f"cart:{cart_id}"
        stock_key = f"stock:available:{product_id}"

        # Get existing quantity and determine NET change required
        existing_item = redis_client.hget(cart_key, product_id)
        existing_quantity = json.loads(existing_item).get('quantity', 0) if existing_item else 0
        
        # Quantity to be decremented from the Redis stock key
        net_quantity_to_reserve = requested_quantity - existing_quantity
        
        # 2. Handle Stock Release (Quantity Reduction)
        if net_quantity_to_reserve < 0:
            released_qty = abs(net_quantity_to_reserve)
            redis_client.incrby(stock_key, released_qty) # Atomically release stock
            net_quantity_to_reserve = 0 
        
        # 3. ATOMIC Stock Reservation Check (for net increase)
        if net_quantity_to_reserve > 0:
            # DECRBY returns the new value. If less than zero, we failed.
            new_stock_level = redis_client.decrby(stock_key, net_quantity_to_reserve)

            if new_stock_level < 0:
                # RESERVATION FAILED: Undo the decrement.
                redis_client.incrby(stock_key, net_quantity_to_reserve)
                logger.warning(f"Stockout: Product {product_id} failed reservation.")
                return JsonResponse({'error': 'Insufficient stock available.'}, status=409)

        # 4. Reservation SUCCESS: Update the Cart Data and TTL
        item_data = {
            "product_id": product_id,
            "product_name": str(data.get('product_name')),
            "quantity": requested_quantity,
            "price": str(data.get('price')),
        }

        redis_client.hset(cart_key, product_id, json.dumps(item_data))
        redis_client.expire(cart_key, CART_TTL_SECONDS) # Set the cart TTL

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

    return JsonResponse({'cart_id': cart_id, 'items': items})


@csrf_exempt
def remove_from_cart(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        cart_id = get_cart_id(request)
        data = json.loads(request.body)
        product_id = str(data.get('product_id'))

        cart_key = f"cart:{cart_id}"
        stock_key = f"stock:available:{product_id}"
        
        # 1. Get the reserved quantity
        reserved_item_json = redis_client.hget(cart_key, product_id)
        if not reserved_item_json:
            return JsonResponse({'message': 'Item not in cart to remove'}, status=404)
            
        reserved_quantity = json.loads(reserved_item_json).get('quantity', 0)

        # 2. Release stock (atomically)
        if reserved_quantity > 0:
            redis_client.incrby(stock_key, reserved_quantity)
            
        # 3. Remove item from cart
        redis_client.hdel(cart_key, product_id)
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
        cart_key = f"cart:{cart_id}"
        
        # 1. Iterate through items to release stock before clearing cart
        items_to_clear = redis_client.hgetall(cart_key)
        for product_id_str, item_json in items_to_clear.items():
            reserved_quantity = json.loads(item_json).get('quantity', 0)
            stock_key = f"stock:available:{product_id_str}"
            if reserved_quantity > 0:
                 redis_client.incrby(stock_key, reserved_quantity) # Atomically release stock
        
        # 2. Clear the cart
        redis_client.delete(cart_key)
        logging.info(f"Cart {cart_id} cleared and stock released.")
        return JsonResponse({'message': 'Cart cleared'}, status=200)
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
        new_quantity = int(data.get('quantity', 1)) # Note: Renamed 'quantity' to 'new_quantity' internally for clarity

        cart_key = f"cart:{cart_id}"
        stock_key = f"stock:available:{product_id}"
        item_json = redis_client.hget(cart_key, product_id)

        if not item_json:
            return JsonResponse({'error': 'Item not found in cart'}, status=404)

        current_item = json.loads(item_json)
        old_quantity = current_item.get('quantity', 0)
        
        # 1. Handle Quantity Reduction (Release Stock)
        if new_quantity <= 0:
            # If new quantity is 0 or less, treat as removal and release all stock.
            if old_quantity > 0:
                redis_client.incrby(stock_key, old_quantity)
            redis_client.hdel(cart_key, product_id)
            logger.info(f"Item {product_id} removed from cart {cart_id} due to quantity <= 0")
            return JsonResponse({'message': 'Item removed due to non-positive quantity', 'cart_id': cart_id})

        # 2. Calculate NET Change
        # Positive result means we need to RELEASE stock (old > new)
        # Negative result means we need to RESERVE stock (old < new)
        net_stock_change = old_quantity - new_quantity

        if net_stock_change > 0:
            # Quantity reduced (e.g., 5 -> 3, net_stock_change = 2). RELEASE stock.
            redis_client.incrby(stock_key, net_stock_change)
            logger.info(f"Released {net_stock_change} stock for product {product_id}")
            
        elif net_stock_change < 0:
            # Quantity increased (e.g., 3 -> 5, net_stock_change = -2). RESERVE stock.
            quantity_to_reserve = abs(net_stock_change)
            
            # ATOMIC CHECK: Decrement the stock counter
            new_stock_level = redis_client.decrby(stock_key, quantity_to_reserve)

            if new_stock_level < 0:
                # RESERVATION FAILED: Undo the decrement and block update.
                redis_client.incrby(stock_key, quantity_to_reserve)
                logger.warning(f"Stockout: Product {product_id} failed to reserve {quantity_to_reserve}.")
                return JsonResponse({'error': 'Insufficient stock available.'}, status=409)
            
            logger.info(f"Reserved {quantity_to_reserve} stock for product {product_id}")


        # 3. Stock Operation Succeeded: Update the Cart Hash
        current_item['quantity'] = new_quantity
        redis_client.hset(cart_key, product_id, json.dumps(current_item))
        
        # Extend cart TTL
        redis_client.expire(cart_key, CART_TTL_SECONDS) 
        
        logging.info(f"Item {product_id} quantity updated to {new_quantity} in cart {cart_id}")
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