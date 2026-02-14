# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CustomerRegistrationSerializer, LoginSerializer,StaffAdminRegistrationSerializer
from rest_framework.permissions import IsAuthenticated
from .authentication import CustomJWTAuthentication
from .permissions import IsAdmin, IsAdminOrStaff, IsStaffAdminOwner, check_admin_or_staff_role
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

    def put(self, request):
        """
        Update customer details. Only customers can update their own data.
        Customers cannot change their mobile_number.
        """
        user_role = request.user.role if hasattr(request.user, 'role') else None
        
        # Only customers can update their details
        if user_role != "customer":
            return Response({
                "status": False,
                "message": "Only customers can update their own details"
            }, status=status.HTTP_403_FORBIDDEN)
        
        unique_id = request.data.get('unique_id')
        
        if not unique_id:
            return Response({
                "status": False,
                "message": "unique_id is required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            customer = RegisteredCustomer.objects.get(unique_id=unique_id)
            # Check if the logged-in user matches the requested unique_id
            log = AllLog.objects.get(unique_id=unique_id)
            if log.phone != request.user.phone:
                return Response({
                    "status": False,
                    "message": "You can only update your own data"
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Check if user is trying to change mobile_number
            if 'mobile_number' in request.data and request.data['mobile_number'] != customer.mobile_number:
                return Response({
                    "status": False,
                    "message": "Mobile number cannot be changed"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update allowed fields
            if 'username' in request.data:
                customer.username = request.data['username']
            if 'state' in request.data:
                customer.state = request.data['state']
            if 'district' in request.data:
                customer.district = request.data['district']
            if 'block' in request.data:
                customer.block = request.data['block']
            
            customer.save()
            
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
                "message": "Customer details updated successfully",
                "data": data
            }, status=status.HTTP_200_OK)
            
        except RegisteredCustomer.DoesNotExist:
            return Response({
                "status": False,
                "message": "Customer not found"
            }, status=status.HTTP_404_NOT_FOUND)


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
    permission_classes = [IsAuthenticated]

    def get(self, request):
        unique_id = request.query_params.get('unique_id')
        
        # Admin can view all staff with is_active field
        if request.user.role == "admin":
            staffs = StaffAdmin.objects.all()
            data = []
            for staff in staffs:
                try:
                    log = AllLog.objects.get(unique_id=staff.unique_id)
                    is_active = log.is_active
                except AllLog.DoesNotExist:
                    is_active = None
                data.append({
                    "id": staff.id,
                    "unique_id": staff.unique_id,
                    "can_name": staff.can_name,
                    "mobile_number": staff.mobile_number,
                    "email_id": staff.email_id,
                    "address": staff.address,
                    "created_at": staff.created_at,
                    "updated_at": staff.updated_at,
                    "is_active": is_active
                })
            return Response({
                "status": True,
                "data": data,
                "count": len(data)
            }, status=status.HTTP_200_OK)
        
        # Staff admin can only view their own data with unique_id
        if request.user.role == "staffadmin":
            if not unique_id:
                return Response({
                    "status": False,
                    "message": "unique_id is required for staff access"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if the unique_id matches the staff member's own unique_id
            if unique_id != request.user.unique_id:
                return Response({
                    "status": False,
                    "message": "You can only access your own data"
                }, status=status.HTTP_403_FORBIDDEN)
            
            try:
                staff = StaffAdmin.objects.get(unique_id=unique_id)
                data = {
                    "id": staff.id,
                    "unique_id": staff.unique_id,
                    "can_name": staff.can_name,
                    "mobile_number": staff.mobile_number,
                    "email_id": staff.email_id,
                    "address": staff.address,
                    "created_at": staff.created_at,
                    "updated_at": staff.updated_at
                }
                return Response({
                    "status": True,
                    "data": data
                }, status=status.HTTP_200_OK)
            except StaffAdmin.DoesNotExist:
                return Response({
                    "status": False,
                    "message": "Staff not found"
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "status": False,
            "message": "Permission denied"
        }, status=status.HTTP_403_FORBIDDEN)

    def post(self, request):
        # Only admin can create staff
        if request.user.role != "admin":
            return Response({
                "status": False,
                "message": "Only admin can create staff"
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = StaffAdminRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response({
                "status": True,
                "message": "Staff admin created successfully"
            }, status=status.HTTP_201_CREATED)

        return Response({
            "status": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        """
        Update staff admin details.
        Staff can update: can_name, email_id, address, can_aadharcard (NOT mobile_number or is_active).
        Admin can update all fields including mobile_number and is_active status.
        """
        user_role = request.user.role if hasattr(request.user, 'role') else None
        
        # Only admin and staffadmin can update
        if user_role not in ["admin", "staffadmin"]:
            return Response({
                "status": False,
                "message": "Only admin and staff can update staff details"
            }, status=status.HTTP_403_FORBIDDEN)
        
        unique_id = request.data.get('unique_id')
        
        if not unique_id:
            return Response({
                "status": False,
                "message": "unique_id is required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            staff = StaffAdmin.objects.get(unique_id=unique_id)
            
            # If staffadmin, verify they are updating their own data
            if user_role == "staffadmin":
                if request.user.unique_id != unique_id:
                    return Response({
                        "status": False,
                        "message": "You can only update your own data"
                    }, status=status.HTTP_403_FORBIDDEN)
                
                # Staffadmin cannot change mobile_number
                if 'mobile_number' in request.data and request.data['mobile_number'] != staff.mobile_number:
                    return Response({
                        "status": False,
                        "message": "Mobile number cannot be changed"
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Staffadmin cannot change is_active
                if 'is_active' in request.data:
                    return Response({
                        "status": False,
                        "message": "You cannot change active status"
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Update allowed fields for staff: can_name, email_id, address, can_aadharcard
                if 'can_name' in request.data:
                    staff.can_name = request.data['can_name']
                if 'email_id' in request.data:
                    # Check if email already exists
                    if AllLog.objects.filter(email=request.data['email_id']).exclude(unique_id=unique_id).exists():
                        return Response({
                            "status": False,
                            "message": "Email already registered"
                        }, status=status.HTTP_400_BAD_REQUEST)
                    staff.email_id = request.data['email_id']
                    # Also update in AllLog
                    try:
                        alllog = AllLog.objects.get(unique_id=unique_id)
                        alllog.email = request.data['email_id']
                        alllog.save()
                    except AllLog.DoesNotExist:
                        pass
                if 'address' in request.data:
                    staff.address = request.data['address']
                if 'can_aadharcard' in request.FILES:
                    staff.can_aadharcard = request.FILES['can_aadharcard']
            
            # Admin can update all fields
            elif user_role == "admin":
                if 'can_name' in request.data:
                    staff.can_name = request.data['can_name']
                if 'address' in request.data:
                    staff.address = request.data['address']
                if 'email_id' in request.data:
                    # Check if email already exists
                    if AllLog.objects.filter(email=request.data['email_id']).exclude(unique_id=unique_id).exists():
                        return Response({
                            "status": False,
                            "message": "Email already registered"
                        }, status=status.HTTP_400_BAD_REQUEST)
                    staff.email_id = request.data['email_id']
                    # Also update in AllLog
                    try:
                        alllog = AllLog.objects.get(unique_id=unique_id)
                        alllog.email = request.data['email_id']
                        alllog.save()
                    except AllLog.DoesNotExist:
                        pass
                if 'can_aadharcard' in request.FILES:
                    staff.can_aadharcard = request.FILES['can_aadharcard']
                if 'mobile_number' in request.data:
                    # Check if mobile number already exists
                    if StaffAdmin.objects.filter(mobile_number=request.data['mobile_number']).exclude(unique_id=unique_id).exists():
                        return Response({
                            "status": False,
                            "message": "Mobile number already registered"
                        }, status=status.HTTP_400_BAD_REQUEST)
                    staff.mobile_number = request.data['mobile_number']
                    # Also update in AllLog
                    try:
                        alllog = AllLog.objects.get(unique_id=unique_id)
                        alllog.phone = request.data['mobile_number']
                        alllog.save()
                    except AllLog.DoesNotExist:
                        pass
                
                # Update is_active status
                if 'is_active' in request.data:
                    try:
                        alllog = AllLog.objects.get(unique_id=unique_id)
                        alllog.is_active = request.data['is_active']
                        alllog.save()
                    except AllLog.DoesNotExist:
                        pass
            
            staff.save()
            
            # Get is_active status for response
            try:
                alllog = AllLog.objects.get(unique_id=unique_id)
                is_active = alllog.is_active
            except AllLog.DoesNotExist:
                is_active = None
            
            data = {
                "id": staff.id,
                "unique_id": staff.unique_id,
                "can_name": staff.can_name,
                "mobile_number": staff.mobile_number,
                "email_id": staff.email_id,
                "address": staff.address,
                "created_at": staff.created_at,
                "updated_at": staff.updated_at
            }
            
            # Include is_active only for admin
            if user_role == "admin":
                data["is_active"] = is_active
            
            return Response({
                "status": True,
                "message": "Staff details updated successfully",
                "data": data
            }, status=status.HTTP_200_OK)
            
        except StaffAdmin.DoesNotExist:
            return Response({
                "status": False,
                "message": "Staff not found"
            }, status=status.HTTP_404_NOT_FOUND)
