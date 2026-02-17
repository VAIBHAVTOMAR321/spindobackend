# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from .serializers import (CustomerIssueSerializer, CustomerRegistrationSerializer, LoginSerializer, StaffAdminRegistrationSerializer,
                          RegisteredCustomerDetailSerializer, RegisteredCustomerListSerializer,
                          StaffAdminDetailSerializer, StaffAdminListSerializer,VendorRegistrationSerializer,ServiceCategorySerializer,VendorRequestSerializer)
from rest_framework.permissions import IsAuthenticated
from .authentication import CustomJWTAuthentication
from .permissions import (IsAdmin, IsAdminFromAllLog, IsAdminOrCustomerFromAllLog, IsAdminOrStaff, IsCustomerFromAllLog, IsStaffAdminOwner, check_admin_or_staff_role,
                          PERMISSION_DENIED, ONLY_ADMIN_CAN_CREATE_STAFF, ONLY_CUSTOMERS_CAN_UPDATE,
                          ONLY_ADMIN_AND_STAFF_CAN_UPDATE, ONLY_ACCESS_OWN_DATA, ONLY_UPDATE_OWN_DATA,
                          MOBILE_NUMBER_CANNOT_CHANGE, CANNOT_CHANGE_ACTIVE_STATUS, CUSTOMER_NOT_FOUND,
                          STAFF_NOT_FOUND, UNIQUE_ID_REQUIRED, UNIQUE_ID_REQUIRED_FOR_CUSTOMER,
                          UNIQUE_ID_REQUIRED_FOR_STAFF, EMAIL_ALREADY_REGISTERED, 
                          MOBILE_NUMBER_ALREADY_REGISTERED)
from .models import CustomerIssue, StaffAdmin, RegisteredCustomer, AllLog, Vendor,ServiceCategory, VendorRequest

class CustomTokenRefreshView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"status": False, "message": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
            return Response({
                "status": True,
                "access": access_token
            }, status=status.HTTP_200_OK)
        except TokenError as e:
            return Response({
                "status": False,
                "message": "Invalid or expired refresh token"
            }, status=status.HTTP_401_UNAUTHORIZED)
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
        
class ServiceCategoryView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request):
        categories = ServiceCategory.objects.all()
        serializer = ServiceCategorySerializer(categories, many=True)
        return Response({"status": True, "data": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        if not hasattr(request.user, 'role') or request.user.role != "admin":
            return Response({"status": False, "message": "Only admin can create category"}, status=status.HTTP_403_FORBIDDEN)
        serializer = ServiceCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": True, "message": "Category created successfully"}, status=status.HTTP_201_CREATED)
        return Response({"status": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        if not hasattr(request.user, 'role') or request.user.role != "admin":
            return Response({"status": False, "message": "Only admin can update category"}, status=status.HTTP_403_FORBIDDEN)
        category_id = request.data.get('id')
        if not category_id:
            return Response({"status": False, "message": "id is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            category = ServiceCategory.objects.get(id=category_id)
        except ServiceCategory.DoesNotExist:
            return Response({"status": False, "message": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ServiceCategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": True, "message": "Category updated successfully"}, status=status.HTTP_200_OK)
        return Response({"status": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        if not hasattr(request.user, 'role') or request.user.role != "admin":
            return Response({"status": False, "message": "Only admin can delete category"}, status=status.HTTP_403_FORBIDDEN)
        category_id = request.data.get('id')
        if not category_id:
            return Response({"status": False, "message": "id is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            category = ServiceCategory.objects.get(id=category_id)
            category.delete()
            return Response({"status": True, "message": "Category deleted successfully"}, status=status.HTTP_200_OK)
        except ServiceCategory.DoesNotExist:
            return Response({"status": False, "message": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
        
class VendorRequestView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def get(self, request):
        # Only admin can get all requests
        if not hasattr(request.user, 'role') or request.user.role != "admin":
            return Response({"status": False, "message": "Only admin can view requests"}, status=status.HTTP_403_FORBIDDEN)
        requests = VendorRequest.objects.all()
        serializer = VendorRequestSerializer(requests, many=True)
        return Response({"status": True, "data": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        # Only vendor can post
        if not hasattr(request.user, 'role') or request.user.role != "vendor":
            return Response({"status": False, "message": "Only vendor can create request"}, status=status.HTTP_403_FORBIDDEN)
        try:
            vendor = Vendor.objects.get(unique_id=request.user.unique_id)
        except Vendor.DoesNotExist:
            return Response({"status": False, "message": "Vendor not found"}, status=status.HTTP_404_NOT_FOUND)
        data = request.data.copy()
        data['vendor'] = vendor.unique_id
        serializer = VendorRequestSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": True, "message": "Request created successfully"}, status=status.HTTP_201_CREATED)
        return Response({"status": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        # Only admin can update status
        if not hasattr(request.user, 'role') or request.user.role != "admin":
            return Response({"status": False, "message": "Only admin can update request"}, status=status.HTTP_403_FORBIDDEN)
        req_id = request.data.get('id')
        if not req_id:
            return Response({"status": False, "message": "id is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            req = VendorRequest.objects.get(id=req_id)
        except VendorRequest.DoesNotExist:
            return Response({"status": False, "message": "Request not found"}, status=status.HTTP_404_NOT_FOUND)
        if 'status' not in request.data:
            return Response({"status": False, "message": "status is required"}, status=status.HTTP_400_BAD_REQUEST)
        req.status = request.data['status']
        req.save()
        return Response({"status": True, "message": "Request status updated successfully"}, status=status.HTTP_200_OK)

    def delete(self, request):
        # Only admin can delete
        if not hasattr(request.user, 'role') or request.user.role != "admin":
            return Response({"status": False, "message": "Only admin can delete request"}, status=status.HTTP_403_FORBIDDEN)
        req_id = request.data.get('id')
        if not req_id:
            return Response({"status": False, "message": "id is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            req = VendorRequest.objects.get(id=req_id)
            req.delete()
            return Response({"status": True, "message": "Request deleted successfully"}, status=status.HTTP_200_OK)
        except VendorRequest.DoesNotExist:
            return Response({"status": False, "message": "Request not found"}, status=status.HTTP_404_NOT_FOUND)
        
class CustomerIssueAPIView(APIView):

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAdminOrCustomerFromAllLog()]
        elif self.request.method == "POST":
            return [IsCustomerFromAllLog()]
        elif self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsAdminFromAllLog()]
        return []

    def get(self, request):
        if request.user.role == "customer":
            issues = CustomerIssue.objects.filter(user=request.user)
        else:
            issues = CustomerIssue.objects.all()

        serializer = CustomerIssueSerializer(issues, many=True)
        return Response(
            {"status": True, "data": serializer.data},
            status=status.HTTP_200_OK
        )

  
    def post(self, request):
        serializer = CustomerIssueSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(
                {"status": True, "message": "Issue created successfully"},
                status=status.HTTP_201_CREATED
            )

        return Response(
            {"status": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    def put(self, request):
        issue_id = request.data.get("id")
        new_status = request.data.get("status")

        if not issue_id:
            return Response(
                {"status": False, "message": "id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not new_status:
            return Response(
                {"status": False, "message": "status is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            issue = CustomerIssue.objects.get(id=issue_id)
        except CustomerIssue.DoesNotExist:
            return Response(
                {"status": False, "message": "Issue not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # ✅ Validate status choice
        valid_status = dict(CustomerIssue.STATUS_CHOICES).keys()
        if new_status not in valid_status:
            return Response(
                {"status": False, "message": "Invalid status value"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Update ONLY status
        issue.status = new_status
        issue.save(update_fields=["status"])

        return Response(
            {"status": True, "message": "Status updated successfully"},
            status=status.HTTP_200_OK
        )

    def delete(self, request):
        issue_id = request.data.get("id")

        if not issue_id:
            return Response(
                {"status": False, "message": "id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            issue = CustomerIssue.objects.get(id=issue_id)
            issue.delete()
            return Response(
                {"status": True, "message": "Issue deleted successfully"},
                status=status.HTTP_200_OK
            )
        except CustomerIssue.DoesNotExist:
            return Response(
                {"status": False, "message": "Issue not found"},
                status=status.HTTP_404_NOT_FOUND
            )