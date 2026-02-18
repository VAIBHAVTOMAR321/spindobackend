from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.contrib.auth.hashers import make_password

from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.permissions import AllowAny
from .serializers import (CustomerRegistrationSerializer, LoginSerializer, StaffAdminRegistrationSerializer,
                          RegisteredCustomerDetailSerializer, RegisteredCustomerListSerializer,
                          StaffAdminDetailSerializer, StaffAdminListSerializer, StaffIssueSerializer,VendorRegistrationSerializer,ServiceCategorySerializer,ServiceRequestByUserSerializer,VendorRequestSerializer,CustomerIssueSerializer)
from rest_framework.permissions import IsAuthenticated
from .authentication import CustomJWTAuthentication
from .permissions import (IsAdmin, IsAdminFromAllLog, IsAdminOrCustomerFromAllLog, IsAdminOrStaff, IsCustomerFromAllLog, IsStaffAdminFromAllLog, IsStaffAdminOwner, check_admin_or_staff_role,IsAdminOrStaffAdminFromAllLog,
                          PERMISSION_DENIED, ONLY_ADMIN_CAN_CREATE_STAFF, ONLY_CUSTOMERS_CAN_UPDATE,
                          ONLY_ADMIN_AND_STAFF_CAN_UPDATE, ONLY_ACCESS_OWN_DATA, ONLY_UPDATE_OWN_DATA,
                          MOBILE_NUMBER_CANNOT_CHANGE, CANNOT_CHANGE_ACTIVE_STATUS, CUSTOMER_NOT_FOUND,
                          STAFF_NOT_FOUND, UNIQUE_ID_REQUIRED, UNIQUE_ID_REQUIRED_FOR_CUSTOMER,
                          UNIQUE_ID_REQUIRED_FOR_STAFF, EMAIL_ALREADY_REGISTERED, 
                          MOBILE_NUMBER_ALREADY_REGISTERED)
from .models import StaffAdmin, RegisteredCustomer, AllLog, StaffIssue, Vendor,ServiceCategory,VendorRequest,CustomerIssue,ServiceRequestByUser


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
        mobile_number = request.data.get("mobile_number")

        # 🔹 Check duplicate mobile before serializer
        if AllLog.objects.filter(phone=mobile_number).exists():
            return Response({
                "status": False,
                "message": "Mobile number already registered"
            }, status=status.HTTP_400_BAD_REQUEST)

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

        user_role = request.user.role if hasattr(request.user, 'role') else None
        unique_id = request.data.get('unique_id')

        if not unique_id:
            return Response({
                "status": False,
                "message": UNIQUE_ID_REQUIRED
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            customer = RegisteredCustomer.objects.get(unique_id=unique_id)
            alllog = AllLog.objects.get(unique_id=unique_id)

        except RegisteredCustomer.DoesNotExist:
            return Response({
                "status": False,
                "message": CUSTOMER_NOT_FOUND
            }, status=status.HTTP_404_NOT_FOUND)

     
        if user_role == "customer":

        
            if request.user.unique_id != unique_id:
                return Response({
                    "status": False,
                    "message": ONLY_UPDATE_OWN_DATA
                }, status=status.HTTP_403_FORBIDDEN)

       
            if 'mobile_number' in request.data:
                return Response({
                    "status": False,
                    "message": MOBILE_NUMBER_CANNOT_CHANGE
                }, status=status.HTTP_400_BAD_REQUEST)

        
            if 'password' in request.data:
                alllog.password = make_password(request.data['password'])

           
            if 'username' in request.data:
                customer.username = request.data['username']
            if 'state' in request.data:
                customer.state = request.data['state']
            if 'district' in request.data:
                customer.district = request.data['district']
            if 'block' in request.data:
                customer.block = request.data['block']
            if 'email' in request.data:
                customer.email = request.data['email']
                alllog.email = request.data['email']
            if 'image' in request.FILES:
                customer.image = request.FILES['image']

            customer.save()
            alllog.save()

            return Response({
                "status": True,
                "message": "Customer details updated successfully"
            }, status=status.HTTP_200_OK)

        # 🔹 ADMIN LOGIC
        elif user_role == "admin":

            # Admin can update mobile number
            if 'mobile_number' in request.data:
                new_mobile = request.data['mobile_number']

                # Check duplicate
                if RegisteredCustomer.objects.filter(
                    mobile_number=new_mobile
                ).exclude(unique_id=unique_id).exists():
                    return Response({
                        "status": False,
                        "message": MOBILE_NUMBER_ALREADY_REGISTERED
                    }, status=status.HTTP_400_BAD_REQUEST)

                customer.mobile_number = new_mobile
                alllog.phone = new_mobile

            # Admin can update password
            if 'password' in request.data:
                from django.contrib.auth.hashers import make_password
                new_password = make_password(request.data['password'])
                alllog.password = new_password

            customer.save()
            alllog.save()

            return Response({
                "status": True,
                "message": "Customer updated successfully by admin"
            }, status=status.HTTP_200_OK)

        else:
            return Response({
                "status": False,
                "message": "You don't have permission to update"
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
        errors = serializer.errors
        if "mobile_number" in errors:
            return Response({
                "status": False,
                "message": errors["mobile_number"][0]
            }, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "status": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
      
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
                if 'password' in request.data:
                    try:
                        alllog = AllLog.objects.get(unique_id=unique_id)
                        alllog.password = make_password(request.data['password'])
                        alllog.save()
                    except AllLog.DoesNotExist:
                        pass
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
                if 'password' in request.data:
                    try:
                        alllog = AllLog.objects.get(unique_id=unique_id)
                        alllog.password = make_password(request.data['password'])
                        alllog.save()
                    except AllLog.DoesNotExist:
                        pass
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
                        staff.is_active = request.data['is_active']
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
        errors = serializer.errors
        if "mobile_number" in errors:
            return Response({
                "status": False,
                "message": errors["mobile_number"][0]
            }, status=status.HTTP_400_BAD_REQUEST)
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
        user_id = request.query_params.get("unique_id")

        if user_id:
            issues = CustomerIssue.objects.filter(unique_id=user_id)
        else:
            issues = CustomerIssue.objects.all().order_by("-created_at")

        serializer = CustomerIssueSerializer(issues, many=True)
        return Response(
            {"status": True, "data": serializer.data},
            status=status.HTTP_200_OK
        )
    def post(self, request):
        serializer = CustomerIssueSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
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

        if not issue_id:
            return Response(
                {"status": False, "message": "id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            issue = CustomerIssue.objects.get(id=issue_id)
        except CustomerIssue.DoesNotExist:
            return Response(
                {"status": False, "message": "Issue not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 🔹 Use same serializer as POST
        serializer = CustomerIssueSerializer(issue, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": True, "message": "Issue updated successfully"},
                status=status.HTTP_200_OK
            )

        return Response(
            {"status": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
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

        except CustomerIssue.DoesNotExist:
            return Response(
                {"status": False, "message": "Issue not found"},
                status=status.HTTP_404_NOT_FOUND
            )
class ServiceRequestAPIView(APIView):

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        elif self.request.method == "POST":
            return [IsCustomerFromAllLog()]
        elif self.request.method in ["PUT", "PATCH"]:
            return [IsCustomerFromAllLog()]
        elif self.request.method == "DELETE":
            return [IsAdminFromAllLog()]
        return []

    # ðŸ”¹ GET
    def get(self, request):

        if request.user.role == "customer":
            requests = ServiceRequestByUser.objects.filter(
                unique_id=request.user.unique_id
            )

        elif request.user.role in ["admin", "staffadmin"]:
            requests = ServiceRequestByUser.objects.all()

        elif request.user.role == "vendor":
            requests = ServiceRequestByUser.objects.filter(
                assign_to=request.user.unique_id
            )

        else:
            return Response(
                {"status": False, "message": "Not allowed"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ServiceRequestByUserSerializer(requests, many=True)

        return Response(
            {"status": True, "data": serializer.data},
            status=status.HTTP_200_OK
        )

    # ðŸ”¹ POST (Customer Create)
    def post(self, request):

        if request.user.role != "customer":
            return Response(
                {"status": False, "message": "Only customers can create request"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            customer = RegisteredCustomer.objects.get(
                unique_id=request.user.unique_id
            )
        except RegisteredCustomer.DoesNotExist:
            return Response(
                {"status": False, "message": "Customer profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ServiceRequestByUserSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(
                unique_id=request.user.unique_id,
                username=customer.username
            )

            return Response(
                {"status": True, "message": "Request created successfully"},
                status=status.HTTP_201_CREATED
            )

        return Response(
            {"status": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ðŸ”¹ PUT (Customer Update Own Request)
    def put(self, request):

        request_id = request.data.get("id")

        if not request_id:
            return Response(
                {"status": False, "message": "id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            service = ServiceRequestByUser.objects.get(id=request_id)
        except ServiceRequestByUser.DoesNotExist:
            return Response(
                {"status": False, "message": "Request not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Only owner can update
        if service.unique_id != request.user.unique_id:
            return Response(
                {"status": False, "message": "You can update only your request"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Prevent edit after assignment
        if service.status != "pending":
            return Response(
                {"status": False, "message": "Cannot edit after assignment"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ServiceRequestByUserSerializer(
            service,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                {"status": True, "message": "Request updated successfully"},
                status=status.HTTP_200_OK
            )

        return Response(
            {"status": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ðŸ”¹ DELETE (Admin Only)
    def delete(self, request):

        request_id = request.data.get("id")

        if not request_id:
            return Response(
                {"status": False, "message": "id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            service = ServiceRequestByUser.objects.get(id=request_id)
            service.delete()

            return Response(
                {"status": True, "message": "Deleted successfully"},
                status=status.HTTP_200_OK
            )

        except ServiceRequestByUser.DoesNotExist:
            return Response(
                {"status": False, "message": "Request not found"},
                status=status.HTTP_404_NOT_FOUND
            )
class AssignVendorAPIView(APIView):
    permission_classes = [IsAdminOrStaffAdminFromAllLog]

    def post(self, request):
        service_id = request.data.get("service_id")
        vendor_unique_id = request.data.get("vendor_unique_id")

        if not service_id or not vendor_unique_id:
            return Response(
                {"status": False, "message": "service_id and vendor_unique_id required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 🔹 Fetch Service Request
        try:
            service = ServiceRequestByUser.objects.get(id=service_id)
        except ServiceRequestByUser.DoesNotExist:
            return Response(
                {"status": False, "message": "Request not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 🔹 Fetch Vendor from AllLog
        try:
            vendor_alllog = AllLog.objects.get(unique_id=vendor_unique_id, role="vendor")
        except AllLog.DoesNotExist:
            return Response(
                {"status": False, "message": "Vendor not found in AllLog"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 🔹 Fetch Vendor details to get username
        try:
            vendor_obj = Vendor.objects.get(unique_id=vendor_unique_id)
        except Vendor.DoesNotExist:
            return Response(
                {"status": False, "message": "Vendor details not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 🔹 Assign Vendor
        service.assign_to = vendor_alllog.unique_id                # Keep AllLog instance
        service.assigned_to_name = vendor_obj.username # Fetch username from Vendor table

        # 🔹 Assigned By
        service.assigned_by = request.user
        if request.user.role == "admin":
            service.assigned_by_name = "Admin"
        elif request.user.role == "staffadmin":
            try:
                staff = StaffAdmin.objects.get(unique_id=request.user.unique_id)
                service.assigned_by_name = staff.can_name
            except StaffAdmin.DoesNotExist:
                service.assigned_by_name = "Staff Admin"

        service.status = "assigned"
        service.save()

        return Response(
            {"status": True, "message": "Vendor assigned successfully"},
            status=status.HTTP_200_OK
        )


@api_view(['GET'])
def get_services_categories(request):

    # Fetch only accepted records
    services = ServiceCategory.objects.filter(status='accepted')

    category_dict = {}

    for service in services:
        category = service.prod_cate
        subcategory = service.sub_cate

        if category not in category_dict:
            category_dict[category] = set()

        category_dict[category].add(subcategory)

    # Convert to response format
    response_data = [
        {
            "category": category,
            "subcategories": list(subcategories)
        }
        for category, subcategories in category_dict.items()
    ]

    return Response(
        {
            "status": True,
            "data": response_data
        },
        status=status.HTTP_200_OK
    )
@api_view(['GET'])
def get_all_vendors(request):
    vendors = Vendor.objects.all().values('unique_id','username','address','category')

    return Response(
        {
            "status": True,
            "data": list(vendors)
        },
        status=status.HTTP_200_OK
    )
class StaffIssueAPIView(APIView):

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAdminOrStaffAdminFromAllLog()]
        elif self.request.method == "POST":
            return [IsStaffAdminFromAllLog()]
        elif self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsAdminFromAllLog()]
        return []


    def get(self, request):
        user_id = request.query_params.get("unique_id")

        if user_id:
            issues = StaffIssue.objects.filter(unique_id=user_id)
        else:
            issues = StaffIssue.objects.all()

        serializer = StaffIssueSerializer(issues, many=True)
        return Response(
            {"status": True, "data": serializer.data},
            status=status.HTTP_200_OK
        )

   
    def post(self, request):
        serializer = StaffIssueSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": True, "message": "Staff issue created successfully"},
                status=status.HTTP_201_CREATED
            )

        return Response(
            {"status": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

  
    def put(self, request):
        issue_id = request.data.get("id")

        if not issue_id:
            return Response(
                {"status": False, "message": "id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            issue = StaffIssue.objects.get(id=issue_id)
        except StaffIssue.DoesNotExist:
            return Response(
                {"status": False, "message": "Issue not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 🔹 Use same serializer as POST
        serializer = StaffIssueSerializer(issue, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": True, "message": "Issue updated successfully"},
                status=status.HTTP_200_OK
            )

        return Response(
            {"status": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def delete(self, request):
        issue_id = request.data.get("id")

        if not issue_id:
            return Response(
                {"status": False, "message": "id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            issue = StaffIssue.objects.get(id=issue_id)
            issue.delete()
            return Response(
                {"status": True, "message": "Issue deleted successfully"},
                status=status.HTTP_200_OK
            )
        except StaffIssue.DoesNotExist:
            return Response(
                {"status": False, "message": "Issue not found"},
                status=status.HTTP_404_NOT_FOUND
            )
