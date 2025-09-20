# products/views.py
import os
import boto3
from botocore.config import Config
from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

from products.models import Product
from products.serializers import ProductSerializer
from .pagination import ProductPagination 
import logging

from rest_framework.views import APIView
from .serializers import BulkProductCreateSerializer


logger = logging.getLogger(__name__)

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

    # ✅ New custom action to list unique categories
    @action(detail=False, methods=['get'])
    def categories(self, request):
        logger.info("Fetching a list of all unique product categories.")
        # Query the database for a list of unique category names
        categories = Product.objects.values_list('category', flat=True).distinct()
        return Response(categories, status=status.HTTP_200_OK)


    def create(self, request, *args, **kwargs):
        logger.info(f"Received create product request from IP: {request.META.get('REMOTE_ADDR')}")
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            self.perform_create(serializer)
            logger.info(f"Product with ID {serializer.instance.id} created successfully.")
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        logger.warning(f"Invalid data for product creation: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        logger.info(f"Fetching product details for ID: {instance.id}")
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def random(self, request):
        """
        Returns a random selection of products.
        Can be limited by a 'count' query parameter.
        """
        count = request.query_params.get('count', 3)
        try:
            count = int(count)
        except ValueError:
            count = 3  # Default to 3 if count is not a valid number
        
        # order_by('?') gets a random set of objects from the database
        products = Product.objects.all().order_by('?')[:count]
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)    

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
        """
        Generates a pre-signed URL for an S3 PUT operation.
        Expects a JSON body with 'product_id', 'fileName', and 'contentType'.
        """
        product_id = request.data.get('product_id')
        file_name = request.data.get('fileName')
        content_type = request.data.get('contentType')

        if not product_id or not file_name or not content_type:
            logger.warning(f"Bad request: 'product_id', 'fileName', or 'contentType' missing. Data received: {request.data}")
            return Response(
                {"error": "product_id, fileName, and contentType are required."},
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