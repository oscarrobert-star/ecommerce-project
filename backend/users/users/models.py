from django.db import models

class Customer(models.Model):
    cognito_username = models.CharField(max_length=255, unique=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    shipping_address = models.TextField()
    # phone_number = models.CharField(max_length=20)

    class Meta:
        db_table = 'customers'

    def __str__(self):
        return self.name

class AdminUser(models.Model):
    cognito_username = models.CharField(max_length=255, unique=True)
    username = models.CharField(max_length=255)
    role = models.CharField(max_length=100)  # e.g., manager, viewer

    class Meta:
        db_table = 'staff_users'

    def __str__(self):
        return self.name
