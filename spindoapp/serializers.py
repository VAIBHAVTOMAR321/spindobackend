# serializers.py (add this)
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password, make_password
from rest_framework import serializers
from django.db import transaction
from .models import AllLog, RegisteredCustomer, ServiceCategory, StaffAdmin, Vendor,VendorRequest,CustomerIssue,ServiceRequestByUser,StaffIssue,Billing,ContactUs



class LoginSerializer(serializers.Serializer):

    mobile_number = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):

        try:
            user = AllLog.objects.get(phone=data['mobile_number'])
        except AllLog.DoesNotExist:
            raise serializers.ValidationError({
                "mobile_number": "Invalid mobile number"
            })

        if not check_password(data['password'], user.password):
            raise serializers.ValidationError({
                "password": "Invalid password"
            })

        if not user.is_active:
            raise serializers.ValidationError({
                "status": "User is in verification process"
            })

        refresh = RefreshToken()

        refresh['unique_id'] = user.unique_id
        refresh['user_id'] = user.id
        refresh['role'] = user.role

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "role": user.role,
            "unique_id": user.unique_id,
            "mobile_number": user.phone
        }


class CustomerRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = RegisteredCustomer
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'unique_id')

    def validate_mobile_number(self, value):
        if AllLog.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Mobile number already registered")
        return value

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop('password')

       
        customer = RegisteredCustomer.objects.create(**validated_data)

        AllLog.objects.create(
            unique_id=customer.unique_id,
            email=customer.email,
            phone=customer.mobile_number,
            password=make_password(password),
            role="customer"
        )

        return customer

class StaffAdminRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = StaffAdmin
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at','unique_id')

    def validate_mobile_number(self, value):
        if AllLog.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Mobile number already registered")
        return value

    

    @transaction.atomic
    def create(self, validated_data):
        phone = validated_data['mobile_number']
        email = validated_data['email_id']
        staff = StaffAdmin.objects.create(
            can_name=validated_data['can_name'],
            mobile_number=phone,
            email_id=email,
            address=validated_data['address'],
            can_aadharcard=validated_data.get('can_aadharcard', None),
            staff_image=validated_data.get('staff_image'),
        )
        AllLog.objects.create(
            unique_id=staff.unique_id,
            phone=phone,
            email=email,
            password=make_password(validated_data['password']),
            role="staffadmin",
            is_active=False
        )
        return staff


# GET Response Serializers
class RegisteredCustomerDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegisteredCustomer
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at','unique_id')

class RegisteredCustomerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegisteredCustomer
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at','unique_id')

class StaffAdminDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffAdmin
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at','unique_id')

class StaffAdminListSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(required=False, allow_null=True)
    class Meta:
        model = StaffAdmin
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at','unique_id')

class VendorRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    aadhar_card = serializers.FileField(required=False,allow_null=True)
    address = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Vendor
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at','unique_id')

    def validate_mobile_number(self, value):
        if AllLog.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Mobile number already registered")
        return value

    

    @transaction.atomic
    def create(self, validated_data):
        password = make_password(validated_data.pop('password'))
    
        # Remove is_active if coming from request
        validated_data.pop('is_active', None)
    
        vendor = Vendor.objects.create(
            **validated_data,
            password=password,
            is_active=False
        )
    
        AllLog.objects.create(
            unique_id=vendor.unique_id,
            phone=vendor.mobile_number,
            email=vendor.email,
            password=vendor.password,
            role="vendor",
            is_active=False
        )
    
        return vendor
    
class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class VendorRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorRequest
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

class CustomerIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerIssue
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class ServiceRequestByUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceRequestByUser
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
class StaffIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffIssue
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
        
class BillingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Billing
        fields = "__all__"
        read_only_fields = ("bill_id", "bill_pdf", "created_at")
class ContactUsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactUs
        fields = "__all__"