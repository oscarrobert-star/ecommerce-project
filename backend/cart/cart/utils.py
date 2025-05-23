# import json
# import os

# from .redis_client import r

# CART_TTL_SECONDS = int(os.environ.get("CART_TTL_SECONDS", 300))

# def _cart_key(user_id):
#     return f"cart:{user_id}"

# def get_cart(user_id):
#     cart_data = r.get(_cart_key(user_id))
#     return json.loads(cart_data) if cart_data else []

# def add_to_cart(user_id, item):
#     key = _cart_key(user_id)
#     cart = get_cart(user_id)
#     cart.append(item)
#     r.setex(key, CART_TTL_SECONDS, json.dumps(cart))

# def remove_from_cart(user_id, item_id):
#     key = _cart_key(user_id)
#     cart = get_cart(user_id)
#     cart = [i for i in cart if i.get("id") != item_id]
#     r.setex(key, CART_TTL_SECONDS, json.dumps(cart))

# def clear_cart(user_id):
#     r.delete(_cart_key(user_id))

import uuid

def get_cart_id(request):
    cart_id = request.headers.get("X-Cart-ID")
    if not cart_id:
        cart_id = str(uuid.uuid4())
    return cart_id
