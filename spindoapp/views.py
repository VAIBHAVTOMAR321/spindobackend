# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import (CustomerRegistrationSerializer, LoginSerializer, StaffAdminRegistrationSerializer,
                          RegisteredCustomerDetailSerializer, RegisteredCustomerListSerializer,
                          StaffAdminDetailSerializer, StaffAdminListSerializer,VendorRegistrationSerializer)
from rest_framework.permissions import IsAuthenticated
from .authentication import CustomJWTAuthentication
from .permissions import (IsAdmin, IsAdminOrStaff, IsStaffAdminOwner, check_admin_or_staff_role,
                          PERMISSION_DENIED, ONLY_ADMIN_CAN_CREATE_STAFF, ONLY_CUSTOMERS_CAN_UPDATE,
                          ONLY_ADMIN_AND_STAFF_CAN_UPDATE, ONLY_ACCESS_OWN_DATA, ONLY_UPDATE_OWN_DATA,
                          MOBILE_NUMBER_CANNOT_CHANGE, CANNOT_CHANGE_ACTIVE_STATUS, CUSTOMER_NOT_FOUND,
                          STAFF_NOT_FOUND, UNIQUE_ID_REQUIRED, UNIQUE_ID_REQUIRED_FOR_CUSTOMER,
                          UNIQUE_ID_REQUIRED_FOR_STAFF, EMAIL_ALREADY_REGISTERED, 
                          MOBILE_NUMBER_ALREADY_REGISTERED)
from .models import StaffAdmin, RegisteredCustomer, AllLog, Vendor


class CustomerRegistrationView(APIView):


    # authentication_classes = [CustomJWTAuthentication]
    # permission_classes = [IsAuthenticated]

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
            customers = RegisteredCustomer.objects.all()
            serializer = RegisteredCustomerListSerializer(customers, many=True)
            return Response({
                "status": True,
                "data": serializer.data,
                "count": customers.count()
            }, status=status.HTTP_200_OK)

        # If user is customer, return only their own data
        if user_role == "customer":
            if not unique_id:
                return Response({
                    "status": False,
                    "message": UNIQUE_ID_REQUIRED_FOR_CUSTOMER
                }, status=status.HTTP_400_BAD_REQUEST)
            try:
                customer = RegisteredCustomer.objects.get(unique_id=unique_id)
                # Check if the logged-in user matches the requested unique_id
                log = AllLog.objects.get(unique_id=unique_id)
                if log.phone != request.user.phone:
                    return Response({
                        "status": False,
                        "message": ONLY_ACCESS_OWN_DATA
                    }, status=status.HTTP_403_FORBIDDEN)
                
                serializer = RegisteredCustomerDetailSerializer(customer)
                return Response({
                    "status": True,
                    "data": serializer.data
                }, status=status.HTTP_200_OK)
            except RegisteredCustomer.DoesNotExist:
                return Response({
                    "status": False,
                    "message": CUSTOMER_NOT_FOUND
                }, status=status.HTTP_404_NOT_FOUND)
        return Response({
            "status": False,
            "message": PERMISSION_DENIED
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
                "message": ONLY_CUSTOMERS_CAN_UPDATE
            }, status=status.HTTP_403_FORBIDDEN)
        
        unique_id = request.data.get('unique_id')
        
        if not unique_id:
            return Response({
                "status": False,
                "message": UNIQUE_ID_REQUIRED
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            customer = RegisteredCustomer.objects.get(unique_id=unique_id)
            # Check if the logged-in user matches the requested unique_id
            log = AllLog.objects.get(unique_id=unique_id)
            if log.phone != request.user.phone:
                return Response({
                    "status": False,
                    "message": ONLY_UPDATE_OWN_DATA
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Check if user is trying to change mobile_number
            if 'mobile_number' in request.data and request.data['mobile_number'] != customer.mobile_number:
                return Response({
                    "status": False,
                    "message": MOBILE_NUMBER_CANNOT_CHANGE
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
            
            return Response({
                "status": True,
                "message": "Customer details updated successfully"
            }, status=status.HTTP_200_OK)
            
        except RegisteredCustomer.DoesNotExist:
            return Response({
                "status": False,
                "message": CUSTOMER_NOT_FOUND
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
            serializer = StaffAdminRegistrationSerializer(staffs, many=True)
            return Response({
                "status": True,
                "data": serializer.data,
                "count": len(serializer.data)
            }, status=status.HTTP_200_OK)
        
        # Staff admin can only view their own data with unique_id
        if request.user.role == "staffadmin":
            if not unique_id:
                return Response({
                    "status": False,
                    "message": UNIQUE_ID_REQUIRED_FOR_STAFF
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if the unique_id matches the staff member's own unique_id
            if unique_id != request.user.unique_id:
                return Response({
                    "status": False,
                    "message": ONLY_ACCESS_OWN_DATA
                }, status=status.HTTP_403_FORBIDDEN)
            
            try:
                staff = StaffAdmin.objects.get(unique_id=unique_id)
                serializer = StaffAdminDetailSerializer()
                return Response({
                    "status": True,
                    "data": serializer.to_representation(staff)
                }, status=status.HTTP_200_OK)
            except StaffAdmin.DoesNotExist:
                return Response({
                    "status": False,
                    "message": STAFF_NOT_FOUND
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "status": False,
            "message": PERMISSION_DENIED
        }, status=status.HTTP_403_FORBIDDEN)

    def post(self, request):
        # Only admin can create staff
        if request.user.role != "admin":
            return Response({
                "status": False,
                "message": ONLY_ADMIN_CAN_CREATE_STAFF
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
                "message": ONLY_ADMIN_AND_STAFF_CAN_UPDATE
            }, status=status.HTTP_403_FORBIDDEN)
        
        unique_id = request.data.get('unique_id')
        
        if not unique_id:
            return Response({
                "status": False,
                "message": UNIQUE_ID_REQUIRED
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            staff = StaffAdmin.objects.get(unique_id=unique_id)
            
            # If staffadmin, verify they are updating their own data
            if user_role == "staffadmin":
                if request.user.unique_id != unique_id:
                    return Response({
                        "status": False,
                        "message": ONLY_UPDATE_OWN_DATA
                    }, status=status.HTTP_403_FORBIDDEN)
                
                # Staffadmin cannot change mobile_number
                if 'mobile_number' in request.data and request.data['mobile_number'] != staff.mobile_number:
                    return Response({
                        "status": False,
                        "message": MOBILE_NUMBER_CANNOT_CHANGE
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Staffadmin cannot change is_active
                if 'is_active' in request.data:
                    return Response({
                        "status": False,
                        "message": CANNOT_CHANGE_ACTIVE_STATUS
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Update allowed fields for staff: can_name, email_id, address, can_aadharcard
                if 'can_name' in request.data:
                    staff.can_name = request.data['can_name']
                if 'email_id' in request.data:
                    # Check if email already exists
                    if AllLog.objects.filter(email=request.data['email_id']).exclude(unique_id=unique_id).exists():
                        return Response({
                            "status": False,
                            "message": EMAIL_ALREADY_REGISTERED
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
                            "message": EMAIL_ALREADY_REGISTERED
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
                            "message": MOBILE_NUMBER_ALREADY_REGISTERED
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
            
            return Response({
                "status": True,
                "message": "Staff details updated successfully"
            }, status=status.HTTP_200_OK)
            
        except StaffAdmin.DoesNotExist:
            return Response({
                "status": False,
                "message": STAFF_NOT_FOUND
            }, status=status.HTTP_404_NOT_FOUND)


class VendorRegistrationView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Only staffadmin can register vendor
        if not hasattr(request.user, 'role') or request.user.role != "staffadmin":
            return Response({
                "status": False,
                "message": "Only staff can register vendors"
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = VendorRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": True,
                "message": "Vendor registered successfully"
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        unique_id = request.query_params.get('unique_id')
        user_role = request.user.role if hasattr(request.user, 'role') else None

        # Admin or staff: get all vendors
        if user_role in ["admin", "staffadmin"]:
            vendors = Vendor.objects.all()
            serializer = VendorRegistrationSerializer(vendors, many=True)
            data = serializer.data
            if user_role == "staffadmin":
                # Remove 'is_active' from each vendor dict for staffadmin
                for item in data:
                     item.pop("is_active", None)
            return Response({
                "status": True,
                "data": data,
                "count": len(data)
            }, status=status.HTTP_200_OK)

        # Vendor: get only own data
        if user_role == "vendor":
            if not unique_id:
                return Response({
                    "status": False,
                    "message": "unique_id is required for vendor access"
                }, status=status.HTTP_400_BAD_REQUEST)
            try:
                vendor = Vendor.objects.get(unique_id=unique_id)
                log = AllLog.objects.get(unique_id=unique_id)
                if log.phone != request.user.phone:
                    return Response({
                        "status": False,
                        "message": "You can only access your own data"
                    }, status=status.HTTP_403_FORBIDDEN)
                serializer = VendorRegistrationSerializer(vendor)
                return Response({
                    "status": True,
                    "data": serializer.data
                }, status=status.HTTP_200_OK)
            except Vendor.DoesNotExist:
                return Response({
                    "status": False,
                    "message": "Vendor not found"
                }, status=status.HTTP_404_NOT_FOUND)
        return Response({
            "status": False,
            "message": "Permission denied"
        }, status=status.HTTP_403_FORBIDDEN)
    
    def put(self, request):
        user_role = request.user.role if hasattr(request.user, 'role') else None
        unique_id = request.data.get('unique_id')

        if not unique_id:
            return Response({
                "status": False,
                "message": "unique_id is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            vendor = Vendor.objects.get(unique_id=unique_id)
            log = AllLog.objects.get(unique_id=unique_id)

            # Vendor can only update own info except mobile_number
            if user_role == "vendor":
                if log.phone != request.user.phone:
                    return Response({
                        "status": False,
                        "message": "You can only update your own data"
                    }, status=status.HTTP_403_FORBIDDEN)
                if 'mobile_number' in request.data and request.data['mobile_number'] != vendor.mobile_number:
                    return Response({
                        "status": False,
                        "message": "Mobile number cannot be changed"
                    }, status=status.HTTP_400_BAD_REQUEST)
                # Update allowed fields
                for field in ['username', 'email', 'state', 'district', 'block', 'address', 'category', 'description']:
                    if field in request.data:
                        setattr(vendor, field, request.data[field])

            # Staff can update all except mobile_number and is_active
            elif user_role == "staffadmin":
                if 'mobile_number' in request.data and request.data['mobile_number'] != vendor.mobile_number:
                    return Response({
                        "status": False,
                        "message": "Mobile number cannot be changed"
                    }, status=status.HTTP_400_BAD_REQUEST)
                if 'is_active' in request.data:
                    return Response({
                        "status": False,
                        "message": "You cannot change active status"
                    }, status=status.HTTP_400_BAD_REQUEST)
                for field in ['username', 'email', 'state', 'district', 'block', 'address', 'category', 'description']:
                    if field in request.data:
                        setattr(vendor, field, request.data[field])

            # Admin can update all fields including mobile_number and is_active
            elif user_role == "admin":
                for field in ['username', 'email', 'state', 'district', 'block', 'address', 'category', 'description']:
                    if field in request.data:
                        setattr(vendor, field, request.data[field])
                if 'mobile_number' in request.data:
                    # Check if mobile number already exists
                    if AllLog.objects.filter(phone=request.data['mobile_number']).exclude(unique_id=unique_id).exists():
                        return Response({
                            "status": False,
                            "message": "Mobile number already registered"
                        }, status=status.HTTP_400_BAD_REQUEST)
                    vendor.mobile_number = request.data['mobile_number']
                    log.phone = request.data['mobile_number']
                    log.save()
                if 'is_active' in request.data:
                    vendor.is_active = request.data['is_active']
                    log.is_active = request.data['is_active']  # <-- Add this line
                    log.save()                                 # <-- And this line
                if 'is_active' in request.data:
                    vendor.is_active = request.data['is_active']

            vendor.save()
            return Response({
                "status": True,
                "message": "Vendor details updated successfully"
            }, status=status.HTTP_200_OK)

        except Vendor.DoesNotExist:
            return Response({
                "status": False,
                "message": "Vendor not found"
            }, status=status.HTTP_404_NOT_FOUND)