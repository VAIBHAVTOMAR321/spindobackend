# models.py

from django.db import models
import uuid


class AllLog(models.Model):

    ROLE_CHOICES = (
    ('customer', 'Customer'),
    ('admin', 'Admin'),
    ('staffadmin', 'Staff Admin'),
)


    id = models.AutoField(primary_key=True)

    unique_id = models.CharField(max_length=50, unique=True)

    phone = models.CharField(max_length=15, unique=True)

    email = models.EmailField(unique=True, null=True, blank=True)

    password = models.CharField(max_length=255)

    role = models.CharField(max_length=50, choices=ROLE_CHOICES)

    is_verified = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)


    USERNAME_FIELD = 'phone'

    REQUIRED_FIELDS = []


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

    unique_id = models.CharField(max_length=50, unique=True,blank=True, null=True)

    username = models.CharField(max_length=150)

    mobile_number = models.CharField(max_length=15, unique=True)

    state = models.CharField(max_length=100)

    district = models.CharField(max_length=100)

    block = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)


    def save(self, *args, **kwargs):

        if not self.unique_id:

            last_customer = RegisteredCustomer.objects.order_by('-id').first()

            if last_customer:
                last_number = int(last_customer.unique_id.split('-')[1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.unique_id = f"USER-{new_number:03d}"

        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.username} ({self.unique_id})"
class StaffAdmin(models.Model):

    id = models.AutoField(primary_key=True)

    unique_id = models.CharField(max_length=50, unique=True)

    can_name = models.CharField(max_length=150 ,null=True, blank=True)

    mobile_number = models.CharField(max_length=15, unique=True)

    email_id = models.EmailField(unique=True, null=True, blank=True)

    address = models.TextField(blank=True, null=True)

    can_aadharcard = models.FileField(upload_to='aadhar_cards/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)


    def save(self, *args, **kwargs):

        if not self.unique_id:

            last = StaffAdmin.objects.order_by('-id').first()

            if last:
                last_number = int(last.unique_id.split('-')[1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.unique_id = f"STAFF-{new_number:03d}"

        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.can_name} ({self.unique_id})"
    
class Vendor(models.Model):
    id = models.AutoField(primary_key=True)
    unique_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    username = models.CharField(max_length=150)
    mobile_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)
    state = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    block = models.CharField(max_length=100)
    password = models.CharField(max_length=255)
    aadhar_card = models.FileField(upload_to='vendor_aadhar/', blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    category = models.JSONField(default=dict)  # For multiple fields
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=False)  # Vendor is inactive by default
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.unique_id:
            last_vendor = Vendor.objects.order_by('-id').first()
            if last_vendor:
                last_number = int(last_vendor.unique_id.split('-')[1])
                new_number = last_number + 1
            else:
                new_number = 1
            self.unique_id = f"VENDOR-{new_number:03d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.unique_id})"
    
class ServiceCategory(models.Model):
    STATUS_CHOICES = (
        ('accepted', 'Accepted'),
        ('draft', 'Draft'),
    )
    id = models.AutoField(primary_key=True)
    prod_name = models.CharField(max_length=255)
    prod_desc = models.TextField(blank=True, null=True)
    prod_img = models.ImageField(upload_to='service_category/', blank=True, null=True)
    prod_cate = models.CharField(max_length=255)
    sub_cate = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.prod_name