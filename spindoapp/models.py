# models.py

from django.db import models
import uuid


class AllLog(models.Model):

    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('admin', 'Admin'),
    )

    id = models.AutoField(primary_key=True)

    unique_id = models.CharField(max_length=50, unique=True, editable=False)

    phone = models.CharField(max_length=15, unique=True)

    password = models.CharField(max_length=255)

    role = models.CharField(max_length=50, choices=ROLE_CHOICES)

    is_verified = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)


    USERNAME_FIELD = 'phone'

    REQUIRED_FIELDS = []


    def save(self, *args, **kwargs):
        if not self.unique_id:
            self.unique_id = "LOG-" + str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.phone} ({self.role})"


    @property
    def is_authenticated(self):
        return True


    @property
    def is_anonymous(self):
        return False



class RegisteredCustomer(models.Model):

    id = models.AutoField(primary_key=True)

    auth_user = models.OneToOneField(AllLog, on_delete=models.CASCADE, related_name="customer_profile")

    username = models.CharField(max_length=150)

    mobile_number = models.CharField(max_length=15, unique=True)

    state = models.CharField(max_length=100)

    district = models.CharField(max_length=100)

    block = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.username
