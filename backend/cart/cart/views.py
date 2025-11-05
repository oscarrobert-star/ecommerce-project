import redis
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .utils import get_cart_id
import logging

logger = logging.getLogger(__name__)

# Redis client
# Assuming REDIS_HOST/PORT are defined in settings
redis_client = redis.StrictRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    decode_responses=True
)

CART_TTL_SECONDS = getattr(settings, "CART_TTL_SECONDS", 900)  # Default to 15 minutes

# ====================================================================
# VIEWS: CART OPERATIONS (Atomic Stock Reservation)
# ====================================================================

@csrf_exempt
def add_to_cart(request):
    if request.method != 'POST':
        logger.warning(f"Invalid method for add_to_cart: {request.method}")
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        # 1. Input/Key Setup
        cart_id = get_cart_id(request)
        data = json.loads(request.body)
        product_id = str(data.get('product_id'))
        requested_quantity = int(data.get('quantity', 1))
        
        logger.info(f"ADD: Cart {cart_id} | Product {product_id} | Req Qty: {requested_quantity}")

        cart_key = f"cart:{cart_id}"
        stock_key = f"stock:available:{product_id}"
        reservation_key = f"reservation:{cart_id}"

        # Get existing quantity to calculate net change
        existing_item = redis_client.hget(cart_key, product_id)
        existing_quantity = json.loads(existing_item).get('quantity', 0) if existing_item else 0
        
        net_quantity_to_reserve = requested_quantity - existing_quantity
        
        # 2. Handle Stock Release (Quantity Reduction - e.g., user changed 5 -> 3)
        if net_quantity_to_reserve < 0:
            released_qty = abs(net_quantity_to_reserve)
            redis_client.incrby(stock_key, released_qty)
            logger.info(f"ADD: RELEASED {released_qty} for P:{product_id} (Cart Qty Reduced)")
            net_quantity_to_reserve = 0 
        
        # 3. ATOMIC Stock Reservation Check (for net increase)
        if net_quantity_to_reserve > 0:
            logger.debug(f"ADD: Attempting atomic DECRBY of {net_quantity_to_reserve} on {stock_key}")
            new_stock_level = redis_client.decrby(stock_key, net_quantity_to_reserve)

            if new_stock_level < 0:
                # RESERVATION FAILED: Undo the decrement.
                redis_client.incrby(stock_key, net_quantity_to_reserve)
                logger.warning(f"ADD: STOCKOUT FAILED. Product {product_id}. Requested: {net_quantity_to_reserve}. Final stock reset.")
                return JsonResponse({'error': 'Insufficient stock available.'}, status=409)

            logger.info(f"ADD: RESERVED {net_quantity_to_reserve} for P:{product_id}. New Redis Stock: {new_stock_level}")

        # 4. Reservation SUCCESS: Update the Cart Data and TTL
        item_data = {
            "product_id": product_id,
            "product_name": str(data.get('product_name')),
            "quantity": requested_quantity,
            "price": str(data.get('price')),
        }

        # Update the temporary cart key (for UI/session) and its TTL
        redis_client.hset(cart_key, product_id, json.dumps(item_data))
        redis_client.expire(cart_key, CART_TTL_SECONDS) 
        
        # Update the persistent reservation key (for stock rollback, NO TTL)
        reservation_data = {"quantity": requested_quantity}
        redis_client.hset(reservation_key, product_id, json.dumps(reservation_data))
        
        logger.info(f"ADD: Cart {cart_id} updated. Item {product_id} set to Qty {requested_quantity}. TTL set.")

        return JsonResponse({'message': 'Item added', 'cart_id': cart_id})

    except json.JSONDecodeError:
        logger.error("ADD: Invalid JSON payload received.")
        return JsonResponse({'error': 'Invalid JSON format.'}, status=400)
    except Exception as e:
        logger.exception(f"ADD: Unhandled error adding item to cart: {e}")
        return JsonResponse({'error': 'Internal server error.'}, status=500)


def get_cart(request):
    logger.info("GET: Retrieving cart details.")
    cart_id = get_cart_id(request)
    redis_key = f"cart:{cart_id}"
    raw_items = redis_client.hgetall(redis_key)

    if not raw_items:
        logger.info(f"GET: Cart {cart_id} not found or empty.")
        return JsonResponse({'message': 'Cart is empty'}, status=404)

    items = []
    for item_json in raw_items.values():
        try:
            items.append(json.loads(item_json))
        except Exception:
            logger.error(f"GET: Failed to parse item JSON in cart {cart_id}.")
            continue

    logger.info(f"GET: Successfully returned cart {cart_id} with {len(items)} items.")
    return JsonResponse({'cart_id': cart_id, 'items': items})


@csrf_exempt
def remove_from_cart(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        cart_id = get_cart_id(request)
        data = json.loads(request.body)
        product_id = str(data.get('product_id'))
        
        logger.info(f"REMOVE: Cart {cart_id} | Product {product_id} | Starting removal process.")

        cart_key = f"cart:{cart_id}"
        stock_key = f"stock:available:{product_id}"
        reservation_key = f"reservation:{cart_id}"
        
        reserved_item_json = redis_client.hget(cart_key, product_id) 
        if not reserved_item_json:
            logger.warning(f"REMOVE: Item {product_id} not found in cart {cart_id}.")
            return JsonResponse({'message': 'Item not in cart to remove'}, status=404)
            
        reserved_quantity = json.loads(reserved_item_json).get('quantity', 0)

        # 2. Release stock (atomically)
        if reserved_quantity > 0:
            redis_client.incrby(stock_key, reserved_quantity)
            logger.info(f"REMOVE: Stock released ({reserved_quantity}) for P:{product_id}. Reservation deleted.")
            
        # 3. Remove item from both cart keys
        redis_client.hdel(cart_key, product_id)
        redis_client.hdel(reservation_key, product_id) 
        
        # If reservation key is now empty, delete it entirely
        if not redis_client.hgetall(reservation_key):
            redis_client.delete(reservation_key)
            logger.info(f"REMOVE: Persistent reservation key {reservation_key} deleted (cart empty).")
            
        return JsonResponse({'message': 'Item removed', 'cart_id': cart_id})
    except json.JSONDecodeError:
        logger.error("REMOVE: Invalid JSON payload received.")
        return JsonResponse({'error': 'Invalid JSON format.'}, status=400)
    except Exception as e:
        logger.exception(f"REMOVE: Unhandled error removing item from cart: {e}")
        return JsonResponse({'error': 'Internal server error.'}, status=500)


@csrf_exempt
def clear_cart(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        cart_id = get_cart_id(request)
        logger.info(f"CLEAR: Starting cart clearing process for {cart_id}.")

        cart_key = f"cart:{cart_id}"
        reservation_key = f"reservation:{cart_id}" 
        
        items_to_clear = redis_client.hgetall(cart_key) 
        total_released = 0

        # 1. Iterate through items to release stock
        for product_id_str, item_json in items_to_clear.items():
            reserved_quantity = json.loads(item_json).get('quantity', 0)
            stock_key = f"stock:available:{product_id_str}"
            if reserved_quantity > 0:
                 redis_client.incrby(stock_key, reserved_quantity)
                 total_released += reserved_quantity
                 
        # 2. Clear both cart and reservation keys
        redis_client.delete(cart_key)
        redis_client.delete(reservation_key) 
        
        logger.info(f"CLEAR: Cart {cart_id} fully cleared. {len(items_to_clear)} items removed. Total stock released: {total_released}.")
        return JsonResponse({'message': 'Cart cleared'}, status=200)
    except Exception as e:
        logger.exception(f"CLEAR: Unhandled error clearing cart: {e}")
        return JsonResponse({'error': 'Internal server error.'}, status=500)


@csrf_exempt
def edit_item_quantity(request):
    if request.method != 'PATCH':
        return JsonResponse({'error': 'Only PATCH allowed'}, status=405)

    try:
        cart_id = get_cart_id(request)
        data = json.loads(request.body)
        product_id = str(data.get('product_id'))
        new_quantity = int(data.get('quantity', 1))
        
        logger.info(f"EDIT: Cart {cart_id} | Product {product_id} | New Qty: {new_quantity}")

        cart_key = f"cart:{cart_id}"
        stock_key = f"stock:available:{product_id}"
        reservation_key = f"reservation:{cart_id}"
        item_json = redis_client.hget(cart_key, product_id)

        if not item_json:
            logger.warning(f"EDIT: Item {product_id} not found in cart {cart_id} during edit.")
            return JsonResponse({'error': 'Item not found in cart'}, status=404)

        current_item = json.loads(item_json)
        old_quantity = current_item.get('quantity', 0)
        net_stock_change = old_quantity - new_quantity # Positive=Release, Negative=Reserve
        
        # 1. Handle Quantity Reduction or Removal (Release Stock)
        if new_quantity <= 0:
            if old_quantity > 0:
                redis_client.incrby(stock_key, old_quantity)
                logger.info(f"EDIT: RELEASED {old_quantity} (removal).")

            redis_client.hdel(cart_key, product_id)
            redis_client.hdel(reservation_key, product_id)
            
            if not redis_client.hgetall(reservation_key):
                redis_client.delete(reservation_key)
                
            logger.info(f"EDIT: Item {product_id} removed from cart {cart_id}.")
            return JsonResponse({'message': 'Item removed due to non-positive quantity', 'cart_id': cart_id})

        if net_stock_change > 0:
            # Quantity reduced (RELEASE stock)
            redis_client.incrby(stock_key, net_stock_change)
            logger.info(f"EDIT: RELEASED {net_stock_change} stock for P:{product_id} (Reduced Qty).")
            
        elif net_stock_change < 0:
            # Quantity increased (RESERVE stock)
            quantity_to_reserve = abs(net_stock_change)
            logger.debug(f"EDIT: Attempting atomic DECRBY of {quantity_to_reserve} on {stock_key} (Increased Qty).")

            new_stock_level = redis_client.decrby(stock_key, quantity_to_reserve)

            if new_stock_level < 0:
                redis_client.incrby(stock_key, quantity_to_reserve)
                logger.warning(f"EDIT: STOCKOUT FAILED. Product {product_id}. Requested: {quantity_to_reserve}.")
                return JsonResponse({'error': 'Insufficient stock available.'}, status=409)
            
            logger.info(f"EDIT: RESERVED {quantity_to_reserve} stock for P:{product_id}. New Redis Stock: {new_stock_level}")


        # 3. Stock Operation Succeeded: Update BOTH Cart Hashes
        current_item['quantity'] = new_quantity
        redis_client.hset(cart_key, product_id, json.dumps(current_item))
        
        reservation_data = {"quantity": new_quantity}
        redis_client.hset(reservation_key, product_id, json.dumps(reservation_data))
        
        redis_client.expire(cart_key, CART_TTL_SECONDS) 
        
        logger.info(f"EDIT: Cart {cart_id} updated. Item {product_id} set to Qty {new_quantity}. TTL extended.")
        return JsonResponse({'message': 'Item quantity updated', 'cart_id': cart_id})
        
    except json.JSONDecodeError:
        logger.error("EDIT: Invalid JSON payload received.")
        return JsonResponse({'error': 'Invalid JSON format.'}, status=400)
    except Exception as e:
        logger.exception(f"EDIT: Unhandled error updating item quantity: {e}")
        return JsonResponse({'error': 'Internal server error.'}, status=500)


# ====================================================================
# VIEWS: CRON/CLEANUP (Deferred Stock Release)
# ====================================================================

@csrf_exempt
def cleanup_expired_reservations(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    logger.info("CRON: Starting check for dangling reservations.")
    
    reservation_keys = redis_client.keys("reservation:*") 
    
    cleanup_count = 0
    stock_released_count = 0
    total_reservations_checked = len(reservation_keys)

    for i, res_key in enumerate(reservation_keys):
        cart_id = res_key.split(':', 1)[1] 
        cart_key = f"cart:{cart_id}"
        
        # Check for the existence of the corresponding display/session cart key
        if not redis_client.exists(cart_key):
            logger.warning(f"CRON: DANGLING RESERVATION found for Cart ID: {cart_id} (Key {i+1}/{total_reservations_checked}). Releasing stock.")
            
            reserved_items = redis_client.hgetall(res_key)
            
            for product_id_str, item_json in reserved_items.items():
                try:
                    reserved_quantity = json.loads(item_json).get('quantity', 0) 
                    stock_key = f"stock:available:{product_id_str}"
                    
                    if reserved_quantity > 0:
                         redis_client.incrby(stock_key, reserved_quantity) 
                         stock_released_count += reserved_quantity
                         logger.debug(f"CRON: Released {reserved_quantity} of P:{product_id_str}.")
                         
                except Exception as e:
                    logger.error(f"CRON: Error releasing stock for P:{product_id_str} in expired cart {cart_id}: {e}")
                    continue
            
            # Delete the persistent reservation key after cleanup
            redis_client.delete(res_key)
            cleanup_count += 1
            logger.info(f"CRON: Cleanup successful for expired cart: {cart_id}. Persistent reservation removed.")

    logger.info(f"CRON: Run Complete. {total_reservations_checked} reservations checked. {cleanup_count} carts cleaned. {stock_released_count} total units released.")
    return JsonResponse({
        "status": "Cleanup complete", 
        "carts_cleaned": cleanup_count,
        "units_released": stock_released_count
    }, status=200)

# ====================================================================
# VIEWS: HEALTH/UTILITY
# ====================================================================

def health_check(request):
    logger.info("HEALTH: Checking Redis and service status.")
    try:
        if not redis_client.ping():
            logger.error("HEALTH: Redis is not reachable.")
            raise Exception("Redis is not reachable")
        
        logger.info("HEALTH: Status OK.")
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        logger.exception(f"HEALTH: Check failed with error {e}")
        return JsonResponse({'status': 'error', 'details': 'Redis failure.'}, status=500)

def get_cart_ttl(request):
    logger.info("TTL: Retrieving cart TTL.")
    try:
        cart_id = get_cart_id(request)
        redis_key = f"cart:{cart_id}"
        ttl = redis_client.ttl(redis_key)
        
        if ttl < 0:
            ttl = 0
            
        logger.info(f"TTL: Cart {cart_id} has {ttl} seconds remaining.")
        return JsonResponse({'ttl': ttl})
    except Exception as e:
        logger.exception(f"TTL: Failed to get cart TTL: {e}")
        return JsonResponse({'error': 'Internal server error.'}, status=500)
