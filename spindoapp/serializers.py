# serializers.py (add this)
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password, make_password
from rest_framework import serializers
from django.db import transaction
from .models import AllLog, RegisteredCustomer, StaffAdmin


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


class CustomerRegistrationSerializer(serializers.Serializer):

    username = serializers.CharField()
    mobile_number = serializers.CharField()
    state = serializers.CharField()
    district = serializers.CharField()
    block = serializers.CharField()
    password = serializers.CharField(write_only=True)


    def validate_mobile_number(self, value):

        if AllLog.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Mobile number already registered")

        return value


    @transaction.atomic
    def create(self, validated_data):

        phone = validated_data['mobile_number']

        # STEP 1: Create RegisteredCustomer (auto generates USER-001)
        customer = RegisteredCustomer.objects.create(
            username=validated_data['username'],
            mobile_number=phone,
            state=validated_data['state'],
            district=validated_data['district'],
            block=validated_data['block'],
        )

        # STEP 2: Create AllLog with same unique_id
        AllLog.objects.create(
            unique_id=customer.unique_id,
            phone=phone,
            password=make_password(validated_data['password']),
            role="customer"
        )

        return customer

class StaffAdminRegistrationSerializer(serializers.Serializer):

    can_name = serializers.CharField()
    mobile_number = serializers.CharField()
    email_id = serializers.EmailField()
    address = serializers.CharField()
    password = serializers.CharField(write_only=True)
    can_aadharcard = serializers.FileField()


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

        # Create StaffAdmin
        staff = StaffAdmin.objects.create(
            can_name=validated_data['can_name'],
            mobile_number=phone,
            email_id=email,
            address=validated_data['address'],
            can_aadharcard=validated_data['can_aadharcard'],
        )

        # Create AllLog
        AllLog.objects.create(
            unique_id=staff.unique_id,
            phone=phone,
            email=email,
            password=make_password(validated_data['password']),
            role="staffadmin",
            is_active=False
        )

        return staff