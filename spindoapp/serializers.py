from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password, make_password
from rest_framework import serializers
from django.db import transaction
from .models import AllLog, RegisteredCustomer, ServiceCategory, StaffAdmin, Vendor, VendorRequest


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
        read_only_fields = ('id', 'created_at', 'updated_at','unique_id')

    def validate_mobile_number(self, value):
        if AllLog.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Mobile number already registered")
        return value

    @transaction.atomic
    def create(self, validated_data):
        phone = validated_data['mobile_number']
        customer = RegisteredCustomer.objects.create(
            username=validated_data['username'],
            mobile_number=phone,
            state=validated_data['state'],
            district=validated_data['district'],
            block=validated_data['block'],
        )
        AllLog.objects.create(
            unique_id=customer.unique_id,
            phone=phone,
            password=make_password(validated_data['password']),
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

    def validate_email_id(self, value):
        if AllLog.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
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
    aadhar_card = serializers.FileField(required=False)
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

    def validate_email(self, value):
        if AllLog.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value

    @transaction.atomic
    def create(self, validated_data):
        password = make_password(validated_data.pop('password'))
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
        read_only_fields = ('id', 'created_at', 'updated_at', 'status')