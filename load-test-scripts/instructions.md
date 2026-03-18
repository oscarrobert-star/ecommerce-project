Stock Flow Load Test Instructions

This script runs a high-concurrency load test simulating a full order-to-payment commit flow to verify the atomic stock reduction in your services.

Target: Up to 10,000 concurrent transactions.

1. Prerequisites

Python: Ensure Python 3.8+ is installed.

Requests Library: Install the required Python library.

pip install requests


Service Connectivity: Ensure all your Docker containers/services are running and accessible from where you run this script.

2. Configuration

The script uses environment variables to find your services.

Service

Environment Variable

Example Default

Product Service

PRODUCT_SERVICE_URL

http://localhost:8001

Cart Service

CART_SERVICE_URL

http://localhost:8002

Checkout Service

CHECKOUT_SERVICE_URL

http://localhost:8003

Order Service

ORDERS_SERVICE_URL

http://localhost:8004

If your services are running in Docker/Kubernetes, you must set these URLs to the internal service names/ports (e.g., http://product-service:8000).

Example (Setting environment variables):

If your services are running locally on these ports:

export PRODUCT_SERVICE_URL="[http://127.0.0.1:8001](http://127.0.0.1:8001)"
export CART_SERVICE_URL="[http://127.0.0.1:8002](http://127.0.0.1:8002)"
export CHECKOUT_SERVICE_URL="[http://127.0.0.1:8003](http://127.0.0.1:8003)"
export ORDERS_SERVICE_URL="[http://127.0.0.1:8004](http://127.0.0.1:8004)"


3. Execution

Run the script directly from your terminal:

python load_test_stock_flow.py


4. Expected Outcome

The script will report the following key metrics:

Successful transactions: Should ideally be equal to NUM_USERS (10,000). Failures indicate race conditions during Redis reservation (409 Conflict) or database commit errors.

Actual Final Stock: This number must exactly equal the Expected Final Stock.

If Actual Final Stock equals Expected Final Stock, it confirms that the multi-stage atomic locking and commit process (Redis reservation followed by DB lock/update) functioned correctly under load.