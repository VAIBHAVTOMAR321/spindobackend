# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CustomerRegistrationSerializer, LoginSerializer,StaffAdminRegistrationSerializer
from rest_framework.permissions import IsAuthenticated
from .authentication import CustomJWTAuthentication
from .permissions import IsAdmin, IsAdminOrStaff, check_admin_or_staff_role
from .models import StaffAdmin, RegisteredCustomer, AllLog


class CustomerRegistrationView(APIView):


    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CustomerRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": True,
                "message": "Customer registered successfully"
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        unique_id = request.query_params.get('unique_id')
        user_role = request.user.role if hasattr(request.user, 'role') else None

        # If user is admin or staff, return all users
        if check_admin_or_staff_role(request.user):
            customers = RegisteredCustomer.objects.all().values(
                'id', 'unique_id', 'username', 'mobile_number', 'state', 'district', 'block', 'created_at', 'updated_at'
            )
            return Response({
                "status": True,
                "data": list(customers),
                "count": customers.count()
            }, status=status.HTTP_200_OK)

        # If user is customer, return only their own data
        if user_role == "customer":
            if not unique_id:
                return Response({
                    "status": False,
                    "message": "unique_id is required for customer access"
                }, status=status.HTTP_400_BAD_REQUEST)
            try:
                customer = RegisteredCustomer.objects.get(unique_id=unique_id)
                # Check if the logged-in user matches the requested unique_id
                log = AllLog.objects.get(unique_id=unique_id)
                if log.phone != request.user.phone:
                    return Response({
                        "status": False,
                        "message": "You can only access your own data"
                    }, status=status.HTTP_403_FORBIDDEN)
                data = {
                    "id": customer.id,
                    "unique_id": customer.unique_id,
                    "username": customer.username,
                    "mobile_number": customer.mobile_number,
                    "state": customer.state,
                    "district": customer.district,
                    "block": customer.block,
                    "created_at": customer.created_at,
                    "updated_at": customer.updated_at
                }
                return Response({
                    "status": True,
                    "data": data
                }, status=status.HTTP_200_OK)
            except RegisteredCustomer.DoesNotExist:
                return Response({
                    "status": False,
                    "message": "Customer not found"
                }, status=status.HTTP_404_NOT_FOUND)
        return Response({
            "status": False,
            "message": "Permission denied"
        }, status=status.HTTP_403_FORBIDDEN)


class LoginView(APIView):

    def post(self, request):

        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            return Response({
                "status": True,
                "message": "Login successful",
                "data": serializer.validated_data
            }, status=status.HTTP_200_OK)

        return Response({
            "status": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class StaffAdminRegistrationView(APIView):

    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        
        # Check permission for GET (admin and staff only)
        if not IsAdminOrStaff().has_permission(request, self):
            return Response({
                "status": False,
                "message": "Only admin and staff can view staff records"
            }, status=status.HTTP_403_FORBIDDEN)

        staffs = StaffAdmin.objects.all().values(
            'id', 'unique_id', 'can_name', 'mobile_number', 
            'email_id', 'address', 'created_at', 'updated_at'
        )

        return Response({
            "status": True,
            "data": list(staffs),
            "count": staffs.count()
        }, status=status.HTTP_200_OK)

    def post(self, request):

        serializer = StaffAdminRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response({
                "status": True,
                "message": "Staff admin created successfully"
            })

        return Response(serializer.errors, status=400)
