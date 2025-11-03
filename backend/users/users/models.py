from django.db import models

class Customer(models.Model):
    cognito_username = models.CharField(max_length=255, unique=True, db_index=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    shipping_address = models.TextField(blank=True)
    # phone_number = models.CharField(max_length=20)

    class Meta:
        db_table = 'customers'

    def __str__(self):
        return self.full_name

class AdminUser(models.Model):
    cognito_username = models.CharField(max_length=255, unique=True, db_index=True)
    username = models.CharField(max_length=255, unique=True)
    role = models.CharField(max_length=100)  # e.g., manager, viewer

    class Meta:
        db_table = 'staff_users'

    def __str__(self):
        return self.username
