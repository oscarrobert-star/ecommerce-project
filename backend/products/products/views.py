# health/views.py
from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError

from rest_framework import viewsets
from products.models import Product
from products.serializers import ProductSerializer
import logging


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import BulkProductCreateSerializer

logger = logging.getLogger(__name__)

# def health_check(request):
#     # Check if the database connection is healthy
#     try:
#         db_conn = connections['db']
#         db_conn.cursor()
#     except OperationalError:
#         return JsonResponse({"status": "unhealthy", "error": "Database is down"}, status=500)

#     return JsonResponse({"status": "healthy"})

def health_check(request):
    logging.info("Health check initiated")
    databases = ["default", "replica"]  # 'default' = write DB, 'replica' = read DB
    status = {}

    for db in databases:
        try:
            connections[db].cursor()
            status[db] = "ok"
        except OperationalError:
            logger.error(f"{db} database connection failed.")
            status[db] = "unreachable"

    return JsonResponse(status)

    
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class BulkProductCreateView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = BulkProductCreateSerializer(data=request.data)
        if serializer.is_valid():
            response_data = serializer.save()
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
