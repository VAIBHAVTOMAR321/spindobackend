# models.py

from django.db import models
import uuid
from datetime import datetime
from django.db.models import Max
import re
class AllLog(models.Model):

    ROLE_CHOICES = (
    ('customer', 'Customer'),
    ('admin', 'Admin'),
    ('staffadmin', 'Staff Admin'),
)


    id = models.AutoField(primary_key=True)
    
    unique_id = models.CharField(max_length=50, unique=True)

    phone = models.CharField(max_length=15, unique=True)

    email = models.EmailField(null=True, blank=True)

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
    email = models.EmailField(null=True, blank=True)
    image = models.ImageField(upload_to='customer_images/', blank=True, null=True)
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
    staff_image = models.ImageField(upload_to='staff_images/',blank=True,null=True)
    can_name = models.CharField(max_length=150 ,null=True, blank=True)

    mobile_number = models.CharField(max_length=15, unique=True)

    email_id = models.EmailField(null=True, blank=True)

    address = models.TextField(blank=True, null=True)
    is_active=models.BooleanField(default=False)
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
    email = models.EmailField( blank=True, null=True)
    state = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    block = models.CharField(max_length=100)
    password = models.CharField(max_length=255)
    aadhar_card = models.FileField(upload_to='vendor_aadhar/', blank=True, null=True)
    vendor_image = models.ImageField(upload_to='vendor_images/',blank=True,null=True)
    address = models.TextField(blank=True, null=True)
    category = models.JSONField(default=dict,blank=True, null=True)  # For multiple fields
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
class VendorRequest(models.Model):
    STATUS_CHOICES = (
    ('accepted', 'Accepted'),
    ('pending', 'Pending'),
    ('rejected', 'Rejected'),
    )
    id = models.AutoField(primary_key=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE,to_field='unique_id')
    username = models.CharField(max_length=150)
    title = models.CharField(max_length=255)
    issue = models.TextField(blank=True, null=True)
    issue_image = models.ImageField(upload_to='vendor_issues/', blank=True, null=True)
    query_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    extra_remark  = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.vendor.unique_id})"
    def save(self, *args, **kwargs):
        if not self.query_id:
            last_query = VendorRequest.objects.aggregate(
                max_query=Max('query_id')
            )['max_query']
    
            if last_query:
                last_number = int(re.search(r'\d+', last_query).group())
                new_number = last_number + 1
            else:
                new_number = 1
    
            self.query_id = f"QUERY-{new_number:03d}"
    
        super().save(*args, **kwargs)
        
class CustomerIssue(models.Model):
    
    STATUS_CHOICES = (
    ('accepted', 'Accepted'),
    ('pending', 'Pending'),
    ('rejected', 'Rejected'),
    )
    query_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    unique_id = models.CharField(max_length=100, blank=True, null=True)
    title = models.CharField(max_length=200, blank=True, null=True)
    issue = models.TextField( blank=True, null=True)
    extra_remark = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    issue_image = models.ImageField(upload_to='customer_issues/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def save(self, *args, **kwargs):
        # Auto-generate query_id if not set
        if not self.query_id:
            last_issue = CustomerIssue.objects.order_by('-id').first()
            if last_issue and last_issue.query_id:
                # Extract number from last query_id
                last_number = int(last_issue.query_id.split('-')[1])
                new_number = last_number + 1
            else:
                new_number = 1
            self.query_id = f"QUERY-{new_number:03d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.title}"
        
class ServiceRequestByUser(models.Model):
    STATUS_CHOICES = (('pending', 'Pending'),('assigned', 'Assigned'),('completed', 'Completed'),('cancelled', 'Cancelled'))
    username = models.CharField(max_length=150,blank=True, null=True)
    request_id = models.CharField(max_length=20,  blank=True)
    unique_id = models.CharField(max_length=50, blank=True, null=True)
    contact_number = models.CharField(max_length=15,blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    state = models.CharField(max_length=100,blank=True, null=True)
    district = models.CharField(max_length=100,blank=True, null=True)
    block = models.CharField(max_length=100,blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    request_for_services = models.JSONField(default=dict,blank=True,null=True)  # For multiple fields
    schedule_date = models.DateField(blank=True, null=True)
    alternate_contact_number = models.CharField(max_length=15, blank=True, null=True)
    schedule_time = models.TimeField(null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='pending')
    assign_to = models.ForeignKey( AllLog,on_delete=models.SET_NULL,null=True,blank=True,to_field='unique_id',related_name="assigned_vendor")
    assigned_to_name = models.CharField(max_length=150, null=True, blank=True)
    assigned_by = models.ForeignKey(AllLog,on_delete=models.SET_NULL,null=True,blank=True, related_name="assigned_by_admin",to_field='unique_id')
    assigned_by_name = models.CharField(max_length=150, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def save(self, *args, **kwargs):

        if not self.request_id:

            last_request = ServiceRequestByUser.objects.order_by('-id').first()

            if last_request and last_request.request_id:
                last_number = int(last_request.request_id.split('-')[1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.request_id = f"REQ-{new_number:03d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.request_id} - {self.username}"
        
        
class StaffIssue(models.Model):

    STATUS_CHOICES = (
    ('accepted', 'Accepted'),
    ('pending', 'Pending'),
    ('rejected', 'Rejected'),
    )

    query_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    unique_id = models.CharField(max_length=100, blank=True, null=True)
    title = models.CharField(max_length=200, blank=True, null=True)
    issue = models.TextField(blank=True, null=True)
    extra_remark = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    issue_image = models.ImageField(upload_to='staff_issues/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.query_id:
            last_issue = StaffIssue.objects.order_by('-id').first()
            if last_issue and last_issue.query_id:
                last_number = int(last_issue.query_id.split('-')[1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.query_id = f"QUERY-{new_number:03d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.title}"
class DistrictBlock(models.Model):
    state = models.CharField(max_length=100, default="Uttarakhand")
    district = models.CharField(max_length=100)
    block = models.CharField(max_length=100)

    class Meta:
        unique_together = ('district', 'block')

    def __str__(self):
        return f"{self.state} - {self.district} - {self.block}"
        
        
class Billing(models.Model):

    bill_id = models.CharField(max_length=30, unique=True, blank=True)
    vendor_id = models.CharField(max_length=70,blank=True, null=True)
    payment_id = models.CharField(max_length=50,blank=True, null=True)

    customer_name = models.CharField(max_length=80,blank=True, null=True)
    cust_mobile = models.CharField(max_length=15,blank=True, null=True)

    service_type = models.CharField(max_length=30,blank=True, null=True)
    service_des = models.CharField(max_length=100,blank=True, null=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    gst = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_payment = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    bill_items=models.JSONField(default=list, blank=True, null=True)
    payment_type = models.CharField(max_length=50,blank=True, null=True)
    bill_pdf = models.FileField(upload_to='bills/', blank=True, null=True)
    bill_date_time= models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(max_length=30)
    def save(self, *args, **kwargs):
        if not self.bill_id:
            current_year = datetime.now().year  # ðŸ‘ˆ Get current year

            # Get last bill of current year only
            last_bill = Billing.objects.filter(
                bill_id__startswith=f"BILL/{current_year}"
            ).order_by('-id').first()

            if last_bill and last_bill.bill_id:
                last_number = int(last_bill.bill_id.split('/')[-1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.bill_id = f"BILL/{current_year}/{new_number:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.bill_id

    def __str__(self):
        return self.bill_id

class ContactUs(models.Model):
    full_name = models.CharField(max_length=100,blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    mobile_number = models.CharField(max_length=15,blank=True, null=True)
    subject = models.CharField(max_length=200,blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.full_name} - {self.subject}"
        