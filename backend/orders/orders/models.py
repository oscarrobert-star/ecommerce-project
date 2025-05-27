from django.db import models

class Order(models.Model):
    customer_id = models.CharField(max_length=100)  # from users service
    payment_status = models.CharField(max_length=20, choices=[
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed")
    ], default="pending")
    shipping_status = models.CharField(max_length=20, choices=[
        ("pending", "Pending"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled")
    ], default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_reference = models.CharField(max_length=255, blank=True, null=True, db_index=True)  # from payment service
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # total amount at time of purchase

    class Meta:
        db_table = 'orders'

    def __str__(self):
        return self.name

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product_id = models.CharField(max_length=100)  # from product service
    product_name = models.CharField(max_length=255)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # price at time of purchase

    class Meta:
        db_table = 'order_items'

    def __str__(self):
        return self.name
