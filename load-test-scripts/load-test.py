import requests
import uuid
import json
import os
import random
import urllib.parse # ADDED: For URL manipulation
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import time
from collections import defaultdict

# --- Configuration ---
# Setting BASE_URL as a fallback for all services
BASE_URL = "https://api.dev.okiyalabs.click"
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", BASE_URL) 
CART_SERVICE_URL = os.getenv("CART_SERVICE_URL", BASE_URL)
CHECKOUT_SERVICE_URL = os.getenv("CHECKOUT_SERVICE_URL", BASE_URL)
ORDERS_SERVICE_URL = os.getenv("ORDERS_SERVICE_URL", BASE_URL)

NUM_USERS = 10000 # Target load for transactions
MAX_WORKERS = 50  # Number of concurrent threads

# Load Test Configuration for Read Phase (set to match transaction load)
READ_LOAD_COUNT = 10000 

# Global variables to be populated dynamically
CATALOG = []
INITIAL_STOCK_MAP = {}
CATALOG_IDS = []

# --- CATALOG LOADING FUNCTION ---

def load_catalog_from_api():
    """Fetches all products from the paginated API and returns the structured catalog data."""
    catalog = []
    current_url = f"{PRODUCT_SERVICE_URL}/products"
    
    print("-> Dynamically loading product catalog from API...")
    
    while current_url and current_url != "null":
        try:
            response = requests.get(current_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract relevant fields and map stock_quantity to initial_stock
            for product in data.get('results', []):
                catalog.append({
                    "id": product.get('id'),
                    "name": product.get('name'),
                    "price": str(product.get('price')), # Ensure price is a string
                    "initial_stock": product.get('stock_quantity')
                })
                
            # Update the URL for the next page
            next_url_raw = data.get('next')
            
            if next_url_raw and next_url_raw != "null":
                # --- SCHEME CORRECTION FIX (Resolves HTTPConnectionPool Error) ---
                parsed_url = urllib.parse.urlparse(next_url_raw)
                
                if parsed_url.scheme == 'http':
                    # If the API returns HTTP for the next page, force it to HTTPS
                    current_url = parsed_url._replace(scheme='https').geturl()
                    print(f"   [FIXED]: Rewriting next page URL to {current_url}")
                elif not parsed_url.netloc and parsed_url.path:
                    # Handle relative URLs
                    current_url = PRODUCT_SERVICE_URL + parsed_url.path
                else:
                    # Use the full URL provided
                    current_url = next_url_raw
            else:
                current_url = None # Break the loop

            if current_url and current_url != "null":
                print(f"   Fetched {len(data['results'])} items. Moving to next page...")
            
        except requests.exceptions.RequestException as e:
            print(f"FATAL: Failed to fetch catalog from {current_url}. Check connectivity and URL. Error: {e}")
            return []
            
    print(f"-> Catalog loading complete. Found {len(catalog)} products.")
    return catalog

# --- Utility Functions ---

def get_product_stock(product_id):
    """Fetches the current stock quantity from the Product service (DB)."""
    try:
        response = requests.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}", timeout=5)
        response.raise_for_status()
        stock_value = response.json().get('stock_quantity')
        return int(stock_value) if stock_value is not None else None
    except Exception:
        return None

# --- READ LOAD TEST FUNCTIONS ---

def read_product_detail(_):
    """Hits a single product detail endpoint randomly."""
    product_id = random.choice(CATALOG_IDS)
    try:
        requests.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}", timeout=5).raise_for_status()
        return True
    except Exception:
        return False

def read_load_phase():
    """Executes a high-volume concurrent read test."""
    print(f"\n--- Phase 1: Starting Read Load Test ({READ_LOAD_COUNT} Requests) ---")
    
    read_start_time = time()
    read_ids = range(READ_LOAD_COUNT)
    
    successful_reads = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(read_product_detail, i) for i in read_ids]
        
        for i, future in enumerate(as_completed(futures)):
            if future.result():
                successful_reads += 1
            
            if (i + 1) % 1000 == 0:
                print(f"  Progress: {i + 1}/{READ_LOAD_COUNT} reads completed ({successful_reads} successful so far)", end='\r')
        
        print(f"  Progress: {READ_LOAD_COUNT}/{READ_LOAD_COUNT} reads completed ({successful_reads} successful total)")

    read_end_time = time()
    read_duration = read_end_time - read_start_time

    print("\n--- Read Load Test Results ---")
    print(f"Total time taken: {read_duration:.2f} seconds")
    print(f"Read Requests/second: {READ_LOAD_COUNT / read_duration:.2f}")
    print(f"Successful Reads: {successful_reads} / {READ_LOAD_COUNT}")

# --- TRANSACTION LOAD TEST FUNCTION ---

def run_user_transaction(user_id):
    """
    Simulates a single user transaction with a randomly selected product.
    Returns: (success: bool, product_id: int | None, error_detail: str)
    """
    
    # Randomly select ONE item for this user's transaction
    selected_item = random.choice(CATALOG)
    product_id = selected_item["id"]
    product_price = selected_item["price"]
    
    # Generate unique ID for the cart and payment
    cart_id = str(uuid.uuid4())
    payment_ref = f"PAY-{uuid.uuid4()}"
    
    # --- STEP 1: ADD TO CART (Stock Reservation in Redis) ---
    cart_url = f"{CART_SERVICE_URL}/cart/add" 
    
    cart_payload = {
        "product_id": str(product_id), 
        "product_name": selected_item["name"],
        "quantity": 1,
        "price": product_price,
    }
    
    try:
        # Pass cart_id as a query parameter
        requests.post(cart_url, params={"cart_id": cart_id}, json=cart_payload, timeout=5).raise_for_status()

        # --- STEP 2: CHECKOUT (Order Creation) ---
        checkout_payload = {
            "email": f"user{user_id}@testload.com",
            "amount": float(product_price), 
            "channel": "test",
            "items": [{
                "product_id": str(product_id),
                "quantity": 1,
                "price": product_price
            }]
        }
        
        checkout_response = requests.post(f"{CHECKOUT_SERVICE_URL}/checkout", json=checkout_payload, timeout=5)
        checkout_response.raise_for_status()
        order_id = checkout_response.json().get("id")

        if not order_id:
            return False, product_id, "Failed to get order_id from checkout."
        
        # --- STEP 3: SIMULATE PAYMENT SUCCESS (Stock Commit) ---
        payment_status_url = f"{ORDERS_SERVICE_URL}/orders/{order_id}/payment_status"
        payment_payload = {
            "payment_status": "paid",
            "payment_reference": payment_ref,
        }
        
        requests.patch(payment_status_url, json=payment_payload, timeout=5).raise_for_status()

        # Success! Return the product ID that was successfully committed
        return True, product_id, None

    except requests.exceptions.HTTPError as e:
        return False, product_id, f"HTTP Error {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return False, product_id, f"General Error: {e}"


def main():
    global CATALOG, INITIAL_STOCK_MAP, CATALOG_IDS
    
    # 1. Dynamically Load Catalog
    CATALOG = load_catalog_from_api()
    if not CATALOG:
        print("FATAL: Cannot proceed without catalog data. Please ensure the API is running and accessible.")
        return

    # 2. Populate global maps
    INITIAL_STOCK_MAP = {p['id']: p['initial_stock'] for p in CATALOG}
    CATALOG_IDS = [p['id'] for p in CATALOG]

    if not CATALOG_IDS:
        print("FATAL: Catalog loaded successfully, but it's empty. Cannot run tests.")
        return
    
    # Run the dedicated Read Load Phase first
    read_load_phase()
    
    print(f"\n--- Phase 2: Starting Transaction Load Test ({NUM_USERS} Transactions) ---")
    transaction_start_time = time()

    # Dictionary to track successful stock reductions per product
    stock_reduction_map = defaultdict(int) 
    
    user_ids = range(NUM_USERS)
    successful_transactions = 0
    failed_transactions = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        futures = [executor.submit(run_user_transaction, user_id) for user_id in user_ids]

        # Process results as they complete and show progress
        for i, future in enumerate(as_completed(futures)):
            success, product_id, detail = future.result()
            
            if success:
                successful_transactions += 1
                stock_reduction_map[product_id] += 1
            else:
                failed_transactions += 1

            # Print progress every 1000 transactions
            if (i + 1) % 1000 == 0:
                print(f"  Progress: {i + 1}/{NUM_USERS} transactions completed ({successful_transactions} successful, {failed_transactions} failed)", end='\r')
        
        # Print final status
        print(f"  Progress: {NUM_USERS}/{NUM_USERS} transactions completed ({successful_transactions} successful total, {failed_transactions} failed total)")

    transaction_end_time = time()
    transaction_duration = transaction_end_time - transaction_start_time

    print("\n--- Transaction Load Test Results ---")
    print(f"Total time taken: {transaction_duration:.2f} seconds")
    print(f"Transactions/second: {NUM_USERS / transaction_duration:.2f}")
    print(f"Successful transactions: {successful_transactions}")
    print(f"Failed transactions: {failed_transactions}")
    
    # --- Phase 3: Final Verification ---
    print("\n--- Final Stock Verification ---")
    overall_success = True
    
    for product_id in CATALOG_IDS:
        committed_count = stock_reduction_map.get(product_id, 0)
        
        # Only check products that were involved in a successful transaction
        if product_id not in stock_reduction_map and committed_count == 0:
            continue
            
        initial_stock = INITIAL_STOCK_MAP.get(product_id, 0)
        expected_stock = initial_stock - committed_count
        actual_final_stock = get_product_stock(product_id)

        if actual_final_stock is None:
            print(f"❌ ERROR: Could not retrieve final stock for Product ID {product_id}. Skipping check.")
            overall_success = False
            continue
        
        if actual_final_stock == expected_stock:
            print(f"  ✅ ID {product_id} ({committed_count} committed): Stock matches.")
        else:
            print(f"  ❌ ID {product_id} ({committed_count} committed): MISMATCH!")
            print(f"     Expected: {expected_stock}, Actual: {actual_final_stock}. Difference: {actual_final_stock - expected_stock} units.")
            overall_success = False

    print("\n===========================================")
    if overall_success and successful_transactions > 0:
        print("✅ SUCCESS: All committed stock quantities match expectations. Atomicity validated.")
    elif successful_transactions == 0:
        print("⚠️ WARNING: Zero successful transactions reported. Cannot validate stock atomicity.")
    else:
        print("❌ FAILURE: Stock mismatch detected in one or more products.")
    print("===========================================")

if __name__ == "__main__":
    main()
