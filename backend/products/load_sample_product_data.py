import requests
import json
import time

# --- Configuration ---
API_ENDPOINT = "https://api.dev.okiyalabs.click/products"
HEADERS = {
    "Content-Type": "application/json"
}

# --- Product Data ---
# Note: Price values have been converted to floats for correctness.
PRODUCTS_DATA = [
    {
        "name": "E-reader",
        "description": "A lightweight, portable device for reading digital books with a glare-free screen.",
        "price": 129.99,
        "stock_quantity": 80,
        "category": "Electronics",
        "image_url": "https://okiyalabs-shop-dest-images.s3.us-east-2.amazonaws.com/1/1-medium.webp"
    },
    {
        "name": "High-Thread-Count Sheets",
        "description": "Luxurious, soft cotton sheets that provide ultimate comfort for a restful sleep.",
        "price": 89.00,
        "stock_quantity": 100,
        "category": "Home",
        "image_url": "https://okiyalabs-shop-dest-images.s3.us-east-2.amazonaws.com/3/3-medium.webp"
    },
    {
        "name": "Smart Thermostat",
        "description": "Control your home's temperature from your phone and save on energy bills.",
        "price": 199.00,
        "stock_quantity": 55,
        "category": "Electronics",
        "image_url": "https://okiyalabs-shop-dest-images.s3.us-east-2.amazonaws.com/5/5-medium.webp"
    },
    {
        "name": "Kitchen Blender",
        "description": "A powerful blender with multiple speed settings for smoothies, soups, and more.",
        "price": 75.00,
        "stock_quantity": 70,
        "category": "Home",
        "image_url": "https://okiyalabs-shop-dest-images.s3.us-east-2.amazonaws.com/7/7-medium.webp"
    },
    {
        "name": "Dune",
        "description": "Frank Herbert's epic science fiction saga exploring politics, religion, and ecology.",
        "price": 12.50,
        "stock_quantity": 180,
        "category": "Books",
        "image_url": "https://okiyalabs-shop-dest-images.s3.us-east-2.amazonaws.com/8/8-medium.webp"
    },
    {
        "name": "Fitness Tracker",
        "description": "Monitor your heart rate, steps, and sleep with this advanced, waterproof fitness band.",
        "price": 65.00,
        "stock_quantity": 110,
        "category": "Electronics",
        "image_url": "https://okiyalabs-shop-dest-images.s3.us-east-2.amazonaws.com/9/9-medium.webp"
    },
    {
        "name": "Wool Scarf",
        "description": "A soft, warm scarf made from 100% natural wool, perfect for cold weather.",
        "price": 24.99,
        "stock_quantity": 90,
        "category": "Clothing",
        "image_url": "https://okiyalabs-shop-dest-images.s3.us-east-2.amazonaws.com/10/10-medium.webp"
    },
    {
        "name": "Decorative Throw Pillows",
        "description": "Add a touch of color and comfort to your living space with these stylish pillows.",
        "price": 30.00,
        "stock_quantity": 220,
        "category": "Home",
        "image_url": "https://okiyalabs-shop-dest-images.s3.us-east-2.amazonaws.com/11/11-medium.webp"
    },
    {
        "name": "Denim Jeans",
        "description": "Durable and stylish denim jeans with a modern, straight-leg fit.",
        "price": 59.99,
        "stock_quantity": 141,
        "category": "Clothing",
        "image_url": "https://okiyalabs-shop-dest-images.s3.us-east-2.amazonaws.com/6/6-medium.webp"
    },
    {
        "name": "To Kill a Mockingbird",
        "description": "Harper Lee's Pulitzer Prize-winning story of racial injustice in a small town.",
        "price": 10.99,
        "stock_quantity": 209,
        "category": "Books",
        "image_url": "https://okiyalabs-shop-dest-images.s3.us-east-2.amazonaws.com/12/12-medium.webp"
    },
    {
        "name": "The Great Gatsby",
        "description": "F. Scott Fitzgerald's classic novel about wealth, love, and the American dream.",
        "price": 9.99,
        "stock_quantity": 248,
        "category": "Books",
        "image_url": "https://okiyalabs-shop-dest-images.s3.us-east-2.amazonaws.com/4/4-medium.webp"
    },
    {
        "name": "Classic Leather Jacket",
        "description": "A timeless leather jacket, perfect for any season and style.",
        "price": 149.99,
        "stock_quantity": 39,
        "category": "Clothing",
        "image_url": "https://okiyalabs-shop-dest-images.s3.us-east-2.amazonaws.com/2/2-medium.webp"
    },
    {
        "name": "Hoodie",
        "description": "A comfortable, classic hoodie with a soft fleece lining and a kangaroo pocket.",
        "price": 45.00,
        "stock_quantity": 160,
        "category": "Clothing",
        "image_url": "https://okiyalabs-shop-dest-images.s3.us-east-2.amazonaws.com/14/14-medium.webp"
    },
    {
        "name": "Aromatherapy Diffuser",
        "description": "A silent diffuser that fills your room with the soothing scent of essential oils.",
        "price": 35.00,
        "stock_quantity": 85,
        "category": "Home",
        "image_url": "https://okiyalabs-shop-dest-images.s3.us-east-2.amazonaws.com/15/15-medium.webp"
    },
    {
        "name": "1984",
        "description": "George Orwell's dystopian masterpiece about government surveillance and manipulation.",
        "price": 8.50,
        "stock_quantity": 270,
        "category": "Books",
        "image_url": "https://okiyalabs-shop-dest-images.s3.us-east-2.amazonaws.com/16/16-medium.webp"
    },
    {
        "name": "Gaming Mouse",
        "description": "High-precision gaming mouse with customizable buttons and RGB lighting.",
        "price": 49.99,
        "stock_quantity": 60,
        "category": "Electronics",
        "image_url": "https://okiyalabs-shop-dest-images.s3.us-east-2.amazonaws.com/17/17-medium.webp"
    },
    {
        "name": "Running Shorts",
        "description": "Lightweight and breathable shorts with a quick-dry fabric for maximum performance.",
        "price": 29.99,
        "stock_quantity": 190,
        "category": "Clothing",
        "image_url": "https://okiyalabs-shop-dest-images.s3.us-east-2.amazonaws.com/18/18-medium.webp"
    },
    {
        "name": "Vacuum Cleaner",
        "description": "Powerful vacuum with a bagless design and HEPA filter to capture fine dust.",
        "price": 150.00,
        "stock_quantity": 40,
        "category": "Home",
        "image_url": "https://okiyalabs-shop-dest-images.s3.us-east-2.amazonaws.com/19/19-medium.webp"
    },
    {
        "name": "The Hobbit",
        "description": "J.R.R. Tolkien's fantasy adventure following Bilbo Baggins' journey.",
        "price": 11.99,
        "stock_quantity": 300,
        "category": "Books",
        "image_url": "https://okiyalabs-shop-dest-images.s3.us-east-2.amazonaws.com/20/20-medium.webp"
    },
    {
        "name": "Webcam",
        "description": "Full HD webcam with a built-in microphone, perfect for video conferencing.",
        "price": 39.99,
        "stock_quantity": 105,
        "category": "Electronics",
        "image_url": "https://okiyalabs-shop-dest-images.s3.us-east-2.amazonaws.com/21/21-medium.webp"
    },
    {
        "name": "Formal Dress Shirt",
        "description": "A crisp, cotton dress shirt with a tailored fit, suitable for formal occasions.",
        "price": 65.00,
        "stock_quantity": 70,
        "category": "Clothing",
        "image_url": "https://okiyalabs-shop-dest-images.s3.us-east-2.amazonaws.com/22/22-medium.webp"
    },
    {
        "name": "Memory Foam Mattress Topper",
        "description": "Adds a layer of plush comfort to any mattress, relieving pressure points.",
        "price": 99.00,
        "stock_quantity": 50,
        "category": "Home",
        "image_url": "https://okiyalabs-shop-dest-images.s3.us-east-2.amazonaws.com/23/23-medium.webp"
    },
    {
        "name": "The Hitchhiker's Guide to the Galaxy",
        "description": "Douglas Adams' hilarious sci-fi story about an ordinary man's journey through space.",
        "price": 10.00,
        "stock_quantity": 160,
        "category": "Books",
        "image_url": "https://okiyalabs-shop-dest-images.s3.us-east-2.amazonaws.com/24/24-medium.webp"
    },
    {
        "name": "Portable Power Bank",
        "description": "A high-capacity power bank that can charge your devices on the go.",
        "price": 30.00,
        "stock_quantity": 250,
        "category": "Electronics",
        "image_url": "https://okiyalabs-shop-dest-images.s3.us-east-2.amazonaws.com/25/25-medium.webp"
    },
    {
        "name": "Polo Shirt",
        "description": "A timeless classic, this polo shirt is made from breathable piqué cotton.",
        "price": 35.00,
        "stock_quantity": 180,
        "category": "Clothing",
        "image_url": "https://okiyalabs-shop-dest-images.s3.us-east-2.amazonaws.com/26/26-medium.webp"
    },
    {
        "name": "Robot Vacuum",
        "description": "Automatically cleans your floors with powerful suction and smart navigation.",
        "price": 299.00,
        "stock_quantity": 25,
        "category": "Home",
        "image_url": "https://okiyalabs-shop-dest-images.s3.us-east-2.amazonaws.com/27/27-medium.webp"
    },
    {
        "name": "Sapiens: A Brief History of Humankind",
        "description": "Yuval Noah Harari's best-selling book on the history of humanity from a new perspective.",
        "price": 15.99,
        "stock_quantity": 140,
        "category": "Books",
        "image_url": "https://okiyalabs-shop-dest-images.s3.us-east-2.amazonaws.com/28/28-medium.webp"
    },
    {
        "name": "USB-C Hub",
        "description": "A compact hub that expands your laptop's connectivity with multiple ports.",
        "price": 45.00,
        "stock_quantity": 95,
        "category": "Electronics",
        "image_url": "https://okiyalabs-shop-dest-images.s3.us-east-2.amazonaws.com/29/29-medium.webp"
    },
    {
        "name": "Winter Coat",
        "description": "A warm, insulated coat with a waterproof outer shell, ideal for extreme cold.",
        "price": 180.00,
        "stock_quantity": 35,
        "category": "Clothing",
        "image_url": "https://okiyalabs-shop-dest-images.s3.us-east-2.amazonaws.com/30/30-medium.webp"
    },
    {
        "name": "Wireless Keyboard and Mouse",
        "description": "A sleek, ergonomic duo that provides a clutter-free and efficient workspace.",
        "price": 55.00,
        "stock_quantity": 128,
        "category": "Electronics",
        "image_url": "https://okiyalabs-shop-dest-images.s3.us-east-2.amazonaws.com/13/13-medium.webp"
    }
]

# --- Script Logic ---

print(f"Starting product loading process. Target endpoint: {API_ENDPOINT}")
print("-" * 50)

for index, product in enumerate(PRODUCTS_DATA):
    try:
        # Send the POST request
        response = requests.post(API_ENDPOINT, headers=HEADERS, json=product)
        
        # Check for success (201 Created or 200 OK)
        if response.status_code in [200, 201]:
            print(f"✅ [{index + 1}/{len(PRODUCTS_DATA)}] SUCCESS: '{product['name']}' (Status: {response.status_code})")
        else:
            # Log error status and response text
            print(f"❌ [{index + 1}/{len(PRODUCTS_DATA)}] FAILURE: '{product['name']}' (Status: {response.status_code})")
            try:
                error_details = response.json()
                print(f"  Error Details: {json.dumps(error_details, indent=2)}")
            except json.JSONDecodeError:
                print(f"  Raw Response: {response.text[:200]}...") # Print first 200 chars of raw response

        # Optional: Add a small delay to avoid rate limiting
        # time.sleep(0.1) 

    except requests.exceptions.RequestException as e:
        print(f"⚠️ [{index + 1}/{len(PRODUCTS_DATA)}] CONNECTION ERROR for '{product['name']}': {e}")
        # Stop on serious connection failure
        break

print("-" * 50)
print("Product loading process finished.")