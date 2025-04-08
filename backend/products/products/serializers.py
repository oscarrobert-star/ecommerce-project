# products/serializers.py

from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class BulkProductCreateSerializer(serializers.Serializer):
    products = ProductSerializer(many=True)

    def create(self, validated_data):
        products_data = validated_data.get('products')
        products = [Product(**product_data) for product_data in products_data]
        Product.objects.bulk_create(products)
        return {'message': 'Products created successfully'}