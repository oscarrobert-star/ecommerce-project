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
    """
    Retrieves the cart ID from the request or generates a new one.
    If a user is authenticated, the cart ID is linked to their user ID.
    Otherwise, a new UUID is generated and returned in a custom header.
    """
    # Use the user's ID as the cart ID if authenticated
    if request.user.is_authenticated:
        return str(request.user.id)
    
    # For unauthenticated users, get the cart ID from the custom header
    cart_id = request.headers.get('x-cart-id')
    if not cart_id:
        # Generate a new UUID if no cart ID is provided
        cart_id = str(uuid.uuid4())
    
    return cart_id
