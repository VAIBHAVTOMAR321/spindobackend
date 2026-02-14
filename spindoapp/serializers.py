# serializers.py (add this)

from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from rest_framework import serializers
from .models import AllLog, RegisteredCustomer
from django.contrib.auth.hashers import make_password

class LoginSerializer(serializers.Serializer):

    mobile_number = serializers.CharField()
    password = serializers.CharField()


    def validate(self, data):

        try:
            user = AllLog.objects.get(phone=data['mobile_number'])
        except AllLog.DoesNotExist:
            raise serializers.ValidationError("Invalid mobile number")

        if not check_password(data['password'], user.password):
            raise serializers.ValidationError("Invalid password")

        refresh = RefreshToken()

        refresh['unique_id'] = user.unique_id
        refresh['user_id'] = user.id
        refresh['role'] = user.role

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "role": user.role,
            "unique_id": user.unique_id,
        }

class CustomerRegistrationSerializer(serializers.Serializer):

    username = serializers.CharField()
    mobile_number = serializers.CharField()
    state = serializers.CharField()
    district = serializers.CharField()
    block = serializers.CharField()
    password = serializers.CharField(write_only=True)


    def create(self, validated_data):

        phone = validated_data['mobile_number']

        password = make_password(validated_data['password'])

        # create AllLog entry
        auth_user = AllLog.objects.create(
            phone=phone,
            password=password,
            role="customer"
        )

        # create RegisteredCustomer entry
        customer = RegisteredCustomer.objects.create(
            auth_user=auth_user,
            username=validated_data['username'],
            mobile_number=phone,
            state=validated_data['state'],
            district=validated_data['district'],
            block=validated_data['block'],
        )

        return customer