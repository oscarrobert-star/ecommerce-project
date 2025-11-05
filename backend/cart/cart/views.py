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

# ====================================================================
# VIEWS: CART OPERATIONS
# ====================================================================

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
        reservation_key = f"reservation:{cart_id}" # Persistent key

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

        # A. Update the temporary cart key (for UI/session, with TTL)
        redis_client.hset(cart_key, product_id, json.dumps(item_data))
        redis_client.expire(cart_key, CART_TTL_SECONDS) 
        
        # B. Update the persistent reservation key (for stock rollback, NO TTL)
        reservation_data = {"quantity": requested_quantity}
        redis_client.hset(reservation_key, product_id, json.dumps(reservation_data))

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
        reservation_key = f"reservation:{cart_id}"
        
        # 1. Get the reserved quantity
        reserved_item_json = redis_client.hget(cart_key, product_id) 
        if not reserved_item_json:
            return JsonResponse({'message': 'Item not in cart to remove'}, status=404)
            
        reserved_quantity = json.loads(reserved_item_json).get('quantity', 0)

        # 2. Release stock (atomically)
        if reserved_quantity > 0:
            redis_client.incrby(stock_key, reserved_quantity)
            
        # 3. Remove item from both cart keys
        redis_client.hdel(cart_key, product_id)
        redis_client.hdel(reservation_key, product_id) 
        
        # If reservation key is now empty, delete it entirely
        if not redis_client.hgetall(reservation_key):
            redis_client.delete(reservation_key)
            
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
        reservation_key = f"reservation:{cart_id}" 
        
        # 1. Iterate through items to release stock
        items_to_clear = redis_client.hgetall(cart_key) 
        
        for product_id_str, item_json in items_to_clear.items():
            reserved_quantity = json.loads(item_json).get('quantity', 0)
            stock_key = f"stock:available:{product_id_str}"
            if reserved_quantity > 0:
                 redis_client.incrby(stock_key, reserved_quantity) # Atomically release stock
        
        # 2. Clear both cart and reservation keys
        redis_client.delete(cart_key)
        redis_client.delete(reservation_key) 
        
        logging.info(f"Cart {cart_id} cleared, stock released, and persistent reservation removed.")
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
        new_quantity = int(data.get('quantity', 1))

        cart_key = f"cart:{cart_id}"
        stock_key = f"stock:available:{product_id}"
        reservation_key = f"reservation:{cart_id}"
        item_json = redis_client.hget(cart_key, product_id)

        if not item_json:
            return JsonResponse({'error': 'Item not found in cart'}, status=404)

        current_item = json.loads(item_json)
        old_quantity = current_item.get('quantity', 0)
        
        # 1. Handle Quantity Reduction (Release Stock)
        if new_quantity <= 0:
            if old_quantity > 0:
                redis_client.incrby(stock_key, old_quantity)
            redis_client.hdel(cart_key, product_id)
            redis_client.hdel(reservation_key, product_id)
            
            if not redis_client.hgetall(reservation_key):
                redis_client.delete(reservation_key)
                
            logger.info(f"Item {product_id} removed from cart {cart_id} due to quantity <= 0")
            return JsonResponse({'message': 'Item removed due to non-positive quantity', 'cart_id': cart_id})

        # 2. Calculate NET Change and manage stock atomically
        net_stock_change = old_quantity - new_quantity

        if net_stock_change > 0:
            # Quantity reduced (RELEASE stock)
            redis_client.incrby(stock_key, net_stock_change)
            logger.info(f"Released {net_stock_change} stock for product {product_id}")
            
        elif net_stock_change < 0:
            # Quantity increased (RESERVE stock)
            quantity_to_reserve = abs(net_stock_change)
            new_stock_level = redis_client.decrby(stock_key, quantity_to_reserve)

            if new_stock_level < 0:
                redis_client.incrby(stock_key, quantity_to_reserve)
                logger.warning(f"Stockout: Product {product_id} failed to reserve {quantity_to_reserve}.")
                return JsonResponse({'error': 'Insufficient stock available.'}, status=409)
            
            logger.info(f"Reserved {quantity_to_reserve} stock for product {product_id}")


        # 3. Stock Operation Succeeded: Update BOTH Cart Hashes
        current_item['quantity'] = new_quantity
        redis_client.hset(cart_key, product_id, json.dumps(current_item))
        
        reservation_data = {"quantity": new_quantity} # Update persistent reservation
        redis_client.hset(reservation_key, product_id, json.dumps(reservation_data))
        
        # Extend cart TTL
        redis_client.expire(cart_key, CART_TTL_SECONDS) 
        
        logging.info(f"Item {product_id} quantity updated to {new_quantity} in cart {cart_id}")
        return JsonResponse({'message': 'Item quantity updated', 'cart_id': cart_id})
        
    except Exception as e:
        logging.exception("Failed to update item quantity")
        return JsonResponse({'error': str(e)}, status=500)


# ====================================================================
# VIEWS: CRON/CLEANUP (To be called by External Scheduler)
# ====================================================================

@csrf_exempt
def cleanup_expired_reservations(request):
    """
    Endpoint called by a scheduled job (cron) to release stock from expired carts.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    # 1. Find all persistent reservation keys
    reservation_keys = redis_client.keys("reservation:*") 
    
    cleanup_count = 0
    stock_released_count = 0

    for res_key in reservation_keys:
        cart_id = res_key.split(':', 1)[1] 
        cart_key = f"cart:{cart_id}"
        
        # 2. Check for the existence of the corresponding display/session cart key
        if not redis_client.exists(cart_key):
            logger.info(f"Dangling reservation found for Cart ID: {cart_id}. Releasing stock.")
            
            # 3. Retrieve reserved items from the persistent reservation key
            reserved_items = redis_client.hgetall(res_key)
            
            for product_id_str, item_json in reserved_items.items():
                try:
                    reserved_quantity = json.loads(item_json).get('quantity', 0) 
                    stock_key = f"stock:available:{product_id_str}"
                    
                    if reserved_quantity > 0:
                         redis_client.incrby(stock_key, reserved_quantity) 
                         stock_released_count += reserved_quantity
                         
                except Exception as e:
                    logger.error(f"Error releasing stock for {product_id_str} in expired cart {cart_id}: {e}")
                    continue
            
            # 4. Delete the persistent reservation key after cleanup
            redis_client.delete(res_key)
            cleanup_count += 1
            logger.info(f"Cleanup successful for expired cart: {cart_id}")

    logger.info(f"Cleanup Run Complete: {cleanup_count} carts cleaned. {stock_released_count} total units released.")
    return JsonResponse({
        "status": "Cleanup complete", 
        "carts_cleaned": cleanup_count,
        "units_released": stock_released_count
    }, status=200)

# ====================================================================
# VIEWS: HEALTH/UTILITY
# ====================================================================

def health_check(request):
    try:
        logging.info("Checking Redis health")
        if not redis_client.ping():
            logging.error("Redis is not reachable")
            raise Exception("Redis is not reachable")
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        logging.exception(f"Health check failed with error {e}")
        return JsonResponse({'status': 'error', 'details': str(e)}, status=500)

def get_cart_ttl(request):
    try:
        cart_id = get_cart_id(request)
        redis_key = f"cart:{cart_id}"
        ttl = redis_client.ttl(redis_key)
        
        if ttl < 0:
            ttl = 0
            
        logging.info(f"TTL for cart {cart_id} is {ttl} seconds.")
        return JsonResponse({'ttl': ttl})
    except Exception as e:
        logging.exception("Failed to get cart TTL")
        return JsonResponse({'error': str(e)}, status=500)