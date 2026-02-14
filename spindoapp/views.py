# views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CustomerRegistrationSerializer, LoginSerializer


class CustomerRegistrationView(APIView):

    def post(self, request):

        serializer = CustomerRegistrationSerializer(data=request.data)

        if serializer.is_valid():

            serializer.save()

            return Response({
                "status": True,
                "message": "Customer registered successfully"
            })

        return Response(serializer.errors, status=400)



class LoginView(APIView):

    def post(self, request):

        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():

            return Response({
                "status": True,
                "message": "Login successful",
                "data": serializer.validated_data
            })

        return Response(serializer.errors, status=400)
