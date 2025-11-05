# products/views.py
import os
import boto3
from botocore.config import Config
from django.http import JsonResponse
from django.db import connections, transaction
from django.db.utils import OperationalError
from django.conf import settings 

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView

from products.models import Product
from products.serializers import ProductSerializer, BulkProductCreateSerializer
from .pagination import ProductPagination 
import logging
import redis

logger = logging.getLogger(__name__)

# --- Redis Configuration and Lazy Load Logic ---
REDIS_HOST = getattr(settings, "REDIS_HOST", 'redis')
REDIS_PORT = getattr(settings, "REDIS_PORT", 6379)
PRODUCT_STOCK_CACHE_TTL = 300  # 5 minutes for lazy-loaded stock cache

redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

def get_stock_or_load_from_db(product_id):
    """
    Checks Redis for stock. If missing, loads it from the DB (Lazy Load).
    """
    stock_key = f"stock:available:{product_id}"
    
    # 1. Check Redis
    stock_count_str = redis_client.get(stock_key)
    if stock_count_str is not None:
        logger.debug(f"CACHE HIT: Stock for {product_id} found in Redis.")
        return int(stock_count_str)

    # 2. Cache Miss: Load from DB and populate Redis
    logger.info(f"CACHE MISS: Stock for {product_id} is missing. Loading from DB.")
    try:
        product = Product.objects.get(id=product_id)
        initial_stock = product.stock_quantity 
        
        # 🛑 FIX: Use SETEX (Set and Expire) to guarantee the TTL is set atomically
        # This prevents the key from being created without a TTL.
        redis_client.setex(stock_key, PRODUCT_STOCK_CACHE_TTL, initial_stock) 
        
        logger.info(f"LAZY LOAD SUCCESS: Stock for {product_id} set to {initial_stock} with TTL {PRODUCT_STOCK_CACHE_TTL}s.")
        return initial_stock
    except Product.DoesNotExist:
        logger.error(f"LAZY LOAD FAILURE: Product {product_id} not found in DB.")
        return None

def cache_stock_for_products(product_queryset):
    """
    Pre-loads stock for a list of products into Redis ONLY if the key is missing.
    Uses an efficient MGET/SETEX approach.
    """
    if not product_queryset:
        return

    product_ids = [str(p.id) for p in product_queryset]
    stock_keys = [f"stock:available:{pid}" for pid in product_ids]
    
    logger.info(f"BULK WARMING START: Checking {len(product_ids)} products.")

    # 1. Find keys that are MISSING in Redis
    current_values = redis_client.mget(stock_keys)
    
    pipeline = redis_client.pipeline()
    new_keys_to_set_count = 0
    
    for i, product in enumerate(product_queryset):
        if current_values[i] is None:
            # Key is missing, add it to the pipeline
            stock_key = stock_keys[i]
            initial_stock = product.stock_quantity
            
            # Use SETEX inside the pipeline to set value and TTL atomically.
            pipeline.setex(stock_key, PRODUCT_STOCK_CACHE_TTL, initial_stock)
            new_keys_to_set_count += 1
            logger.debug(f"WARMING: Queued {product.id} (Stock: {initial_stock}) for bulk SETEX.")
        else:
            logger.debug(f"WARMING: Product {product.id} already exists in cache. Skipping.")
    
    if new_keys_to_set_count > 0:
        pipeline.execute()
        logger.info(f"BULK WARMING COMPLETE: Set {new_keys_to_set_count} new stock keys with TTL {PRODUCT_STOCK_CACHE_TTL}s.")
    else:
        logger.info("BULK WARMING COMPLETE: All checked products were already cached.")

# --- Health Check ---
def health_check(request):
    logging.info("Health check initiated")
    databases = ["default", "replica"]
    status = {}

    for db in databases:
        try:
            connections[db].cursor()
            status[db] = "ok"
        except OperationalError:
            logger.error(f"Database '{db}' connection failed.", exc_info=True)
            status[db] = "unreachable"

    return JsonResponse(status)

    
# --- ProductViewSet ---
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    pagination_class = ProductPagination 

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name', None)
        category = self.request.query_params.get('category', None)

        if name is not None:
            queryset = queryset.filter(name__icontains=name)
            logger.info(f"Filtering products by name: '{name}'")
            
        if category is not None:
            queryset = queryset.filter(category__iexact=category)
            logger.info(f"Filtering products by category: '{category}'")

        return queryset

    @action(detail=False, methods=['get'])
    def categories(self, request):
        logger.info("Fetching a list of all unique product categories.")
        categories = Product.objects.values_list('category', flat=True).distinct()
        return Response(categories, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        """Overrides list to trigger Redis cache warming on pagination/filter."""
        logger.info("API CALL: GET /products (List view)")
        if request.META.get('HTTP_X_FORWARDED_PROTO', '').lower() == 'https':
            request.META['wsgi.url_scheme'] = 'https'
        
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            cache_stock_for_products(page)
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        cache_stock_for_products(queryset)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        logger.info("API CALL: POST /products (Create product)")
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            self.perform_create(serializer)
            logger.info(f"Product with ID {serializer.instance.id} created successfully.")
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        logger.warning(f"Invalid data for product creation: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def perform_create(self, serializer):
        instance = serializer.save()
        stock_key = f"stock:available:{instance.id}"
        # 🟢 Option: Immediately cache with TTL instead of just deleting
        redis_client.setex(stock_key, PRODUCT_STOCK_CACHE_TTL, instance.stock_quantity)
        logger.info(f"CACHE PRIMED: Set stock for new product {instance.id} with TTL.")

    def perform_update(self, serializer):
        instance = serializer.save()
        stock_key = f"stock:available:{instance.id}"
        # 🟢 Option: Immediately refresh cache with TTL
        redis_client.setex(stock_key, PRODUCT_STOCK_CACHE_TTL, instance.stock_quantity)
        logger.info(f"CACHE REFRESHED: Updated stock for product {instance.id} with TTL.")

    def retrieve(self, request, *args, **kwargs):
        logger.info("API CALL: GET /products/{id} (Retrieve detail)")
        instance = self.get_object()
        logger.info(f"Fetching product details for ID: {instance.id}")
        get_stock_or_load_from_db(instance.id)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def random(self, request):
        logger.info("API CALL: GET /products/random")
        count = request.query_params.get('count', 3)
        try:
            count = int(count)
        except ValueError:
            count = 3  
        
        products = Product.objects.all().order_by('?')[:count]
        cache_stock_for_products(products)
        
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)    
    
    @action(detail=False, methods=['post'], url_path='current-stock')
    def current_stock(self, request):
        logger.info("API CALL: POST /products/current-stock (Fetching live Redis stock)")
        product_ids = request.data.get('product_ids')
        if not product_ids or not isinstance(product_ids, list):
            return Response({"error": "A list of 'product_ids' is required."}, status=400)
        
        stock_data = {}
        for product_id in product_ids:
            stock_data[product_id] = get_stock_or_load_from_db(product_id) 
            
        return Response(stock_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['patch'])
    def update_stock(self, request):
        logger.info("API CALL: PATCH /products/update_stock (Final Commit/Release)")
        
        items = request.data.get('items', [])
        transaction_type = request.data.get('transaction_type') 

        if not items or transaction_type not in ['COMMIT', 'RELEASE']:
            return Response({"error": "Invalid data or transaction type."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                for item in items:
                    product_id = item.get('product_id')
                    quantity = item.get('quantity')
                    stock_key = f"stock:available:{product_id}"
                    
                    product = Product.objects.select_for_update().get(id=product_id)

                    if transaction_type == 'COMMIT':
                        if product.stock_quantity < quantity:
                            logger.critical(f"CRITICAL: Oversell detected! Product {product_id} DB stock {product.stock_quantity} < requested {quantity}.")
                            raise ValueError(f"Insufficient physical stock for product ID {product_id} at commit.")
                            
                        product.stock_quantity -= quantity 
                        redis_client.delete(stock_key)
                        logger.info(f"STOCK COMMIT: Committed {quantity} of {product_id}. Deleted Redis key.")

                    elif transaction_type == 'RELEASE':
                        product.stock_quantity += quantity
                        redis_client.delete(stock_key)
                        logger.info(f"STOCK RELEASE: Released {quantity} of {product_id}. Deleted Redis key.")
                    
                    product.save()

            return Response({"status": "Stock updated successfully."}, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT) 
        except Product.DoesNotExist:
            logger.error(f"Product not found during stock update: {e}", exc_info=True)
            return Response({"error": "One or more products not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.critical(f"UNHANDLED ERROR: Stock update failed. {e}", exc_info=True)
            return Response({"error": "An internal error occurred during stock update."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BulkProductCreateView(APIView):
    def post(self, request, *args, **kwargs):
        logger.info("Received bulk product creation request.")
        serializer = BulkProductCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                response_data = serializer.save()
                logger.info(f"Bulk creation successful. {len(response_data)} products created.")
                return Response(response_data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Error during bulk product creation: {e}", exc_info=True)
                return Response({"error": "An internal error occurred during bulk creation."},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        logger.warning(f"Invalid data for bulk product creation: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class S3PresignedUrlView(APIView):
    def post(self, request, *args, **kwargs):
        product_id = request.data.get('product_id')
        file_name = request.data.get('fileName')
        content_type = request.data.get('contentType')

        if not product_id or not file_name or not content_type:
            logger.warning(f"Bad request: 'product_id', 'fileName', or 'contentType' missing. Data received: {request.data}")
            return Response(
                {"error": "product_id, fileName, or contentType are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        bucket_name = os.environ.get("IMAGE_BUCKET_NAME")
        if not bucket_name:
            logger.error("IMAGE_BUCKET_NAME environment variable not set.")
            return Response(
                {"error": "S3 bucket configuration error."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        s3_config = Config(
            signature_version='s3v4',
            region_name=os.environ.get("AWS_REGION", "us-east-2") )
        s3_client = boto3.client('s3', config=s3_config)

        try:
            s3_object_key = f"{product_id}/{file_name}"

            presigned_url = s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': bucket_name,
                    'Key': s3_object_key,
                    'ContentType': content_type 
                },
                ExpiresIn=3600  
            )
            logger.info(f"Successfully generated pre-signed URL for S3 key: {s3_object_key}")
            return Response({'uploadUrl': presigned_url}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error generating pre-signed URL for {s3_object_key}: {e}", exc_info=True)
            return Response(
                {"error": "Failed to generate pre-signed URL."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )