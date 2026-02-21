import random
import requests
from shlex import quote
from django.utils import timezone
from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.contrib.auth.hashers import make_password
from .utils_billing import generate_bill_pdf
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.permissions import AllowAny
from .serializers import (CustomerRegistrationSerializer, LoginSerializer, StaffAdminRegistrationSerializer,StaffIssueSerializer,BillingSerializer, ContactUsSerializer,SolarInstallationQuerySerializer,CompanyDetailsItemSerializer,
                          RegisteredCustomerDetailSerializer, RegisteredCustomerListSerializer,
                          StaffAdminDetailSerializer, StaffAdminListSerializer,VendorRegistrationSerializer,ServiceCategorySerializer,ServiceRequestByUserSerializer,VendorRequestSerializer,CustomerIssueSerializer)
from rest_framework.permissions import IsAuthenticated
from .authentication import CustomJWTAuthentication
from .permissions import (IsAdmin, IsAdminFromAllLog, IsAdminOrCustomerFromAllLog, IsAdminOrStaff, IsCustomerFromAllLog, IsStaffAdminOwner, check_admin_or_staff_role,IsAdminOrStaffAdminFromAllLog,IsStaffAdminFromAllLog,
                          PERMISSION_DENIED, ONLY_ADMIN_CAN_CREATE_STAFF, ONLY_CUSTOMERS_CAN_UPDATE,
                          ONLY_ADMIN_AND_STAFF_CAN_UPDATE, ONLY_ACCESS_OWN_DATA, ONLY_UPDATE_OWN_DATA,
                          MOBILE_NUMBER_CANNOT_CHANGE, CANNOT_CHANGE_ACTIVE_STATUS, CUSTOMER_NOT_FOUND,
                          STAFF_NOT_FOUND, UNIQUE_ID_REQUIRED, UNIQUE_ID_REQUIRED_FOR_CUSTOMER,
                          UNIQUE_ID_REQUIRED_FOR_STAFF, EMAIL_ALREADY_REGISTERED, 
                          MOBILE_NUMBER_ALREADY_REGISTERED)
from .models import StaffAdmin, RegisteredCustomer, AllLog, Vendor,ServiceCategory,PhoneOTP,VendorRequest,CustomerIssue,ServiceRequestByUser,StaffIssue,DistrictBlock,Billing, ContactUs,SolarInstallationQuery,CompanyDetailsItem
from django.db import transaction

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

       
        if AllLog.objects.filter(phone=mobile_number, role="customer").exists():
            return Response({
                "status": False,
                "message": "Mobile number already registered for customer"
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
            customers = RegisteredCustomer.objects.all().order_by("-created_at")
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
            staffs = StaffAdmin.objects.all().order_by("-created_at")
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
                if 'password' in request.data:
                    try:
                        alllog = AllLog.objects.get(unique_id=unique_id)
                        alllog.password = make_password(request.data['password'])
                        alllog.save()
                    except AllLog.DoesNotExist:
                        pass
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
                if 'staff_image' in request.FILES:
                    staff.staff_image = request.FILES['staff_image']
                if 'can_aadharcard' in request.FILES:
                    staff.can_aadharcard = request.FILES['can_aadharcard']
            
            # Admin can update all fields
            elif user_role == "admin":
                if 'can_name' in request.data:
                    staff.can_name = request.data['can_name']
                if 'address' in request.data:
                    staff.address = request.data['address']
                if 'staff_image' in request.FILES:
                    staff.staff_image = request.FILES['staff_image']
                if 'email_id' in request.data:
                    staff.email_id = request.data['email_id']
                
                    # Also update in AllLog
                    try:
                        alllog = AllLog.objects.get(unique_id=unique_id)
                        alllog.email = request.data['email_id']
                        alllog.save()
                    except AllLog.DoesNotExist:
                        pass
                if 'password' in request.data:
                    try:
                        alllog = AllLog.objects.get(unique_id=unique_id)
                        alllog.password = make_password(request.data['password'])
                        alllog.save()
                    except AllLog.DoesNotExist:
                        pass
                if 'can_aadharcard' in request.FILES:
                    staff.can_aadharcard = request.FILES['can_aadharcard']
                if 'mobile_number' in request.data:
                    new_mobile = request.data['mobile_number']

                    # Check duplicate ONLY for staffadmin role
                    if AllLog.objects.filter(
                            phone=new_mobile,
                            role="staffadmin"
                    ).exclude(unique_id=unique_id).exists():

                        return Response({
                            "status": False,
                            "message": MOBILE_NUMBER_ALREADY_REGISTERED
                        }, status=status.HTTP_400_BAD_REQUEST)

                    staff.mobile_number = new_mobile

                    try:
                        alllog = AllLog.objects.get(unique_id=unique_id)
                        alllog.phone = new_mobile
                        alllog.save()
                    except AllLog.DoesNotExist:
                        pass
                
                # Update is_active status
                if 'is_active' in request.data:
                    try:
                        alllog = AllLog.objects.get(unique_id=unique_id)
                        staff.is_active = request.data['is_active']
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
            vendors = Vendor.objects.all().order_by("-created_at")
            serializer = VendorRegistrationSerializer(vendors, many=True)
            data = serializer.data
            
                # Remove 'is_active' from each vendor dict for staffadmin
                
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
                if 'aadhar_card' in request.FILES:
                    vendor.aadhar_card = request.FILES['aadhar_card']
                if 'vendor_image' in request.FILES:
                    vendor.vendor_image = request.FILES['vendor_image']
                    
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
                    new_mobile = request.data['mobile_number']

                    if AllLog.objects.filter(
                            phone=new_mobile,
                            role="vendor"
                    ).exclude(unique_id=unique_id).exists():
                        return Response({
                            "status": False,
                            "message": "Mobile number already registered"
                        }, status=status.HTTP_400_BAD_REQUEST)

                    vendor.mobile_number = new_mobile
                    log.phone = new_mobile
                    log.save()
                if 'password' in request.data:
                    log.password = make_password(request.data['password'])
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
        unique_id = request.query_params.get('unique_id')
        user_role = request.user.role if hasattr(request.user, 'role') else None

       
        if user_role == "admin":
            requests = VendorRequest.objects.all()
            serializer = VendorRequestSerializer(requests, many=True)
            return Response({
                "status": True,
                "data": serializer.data,
                "count": requests.count()
            }, status=status.HTTP_200_OK)

       
        if user_role == "vendor":
            if not unique_id:
                return Response({
                    "status": False,
                    "message": "unique_id is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                vendor = Vendor.objects.get(unique_id=unique_id)

              
                if vendor.unique_id != request.user.unique_id:
                    return Response({
                        "status": False,
                        "message": "You can only access your own requests"
                    }, status=status.HTTP_403_FORBIDDEN)

                requests = VendorRequest.objects.filter(vendor=vendor)
                serializer = VendorRequestSerializer(requests, many=True)

                return Response({
                    "status": True,
                    "data": serializer.data,
                    "count": requests.count()
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

    def post(self, request):
        
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
            return [IsAuthenticated()]
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
            requests = ServiceRequestByUser.objects.all().order_by("-created_at")
    
        elif request.user.role == "vendor":
    
            all_requests = ServiceRequestByUser.objects.all().order_by("-created_at")
            vendor_requests = []
    
            for service_request in all_requests:
                if service_request.assignments:
                    for entry in service_request.assignments:
                        # entry format:
                        # [[services], vendor_unique_id, vendor_name]
                        if entry[1] == request.user.unique_id:
                            vendor_requests.append(service_request)
                            break
    
            requests = vendor_requests
    
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

        request_id = request.data.get("request_id")

        if not request_id:
            return Response(
                {"status": False, "message": "id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            service = ServiceRequestByUser.objects.get(request_id=request_id)
        except ServiceRequestByUser.DoesNotExist:
            return Response(
                {"status": False, "message": "Request not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        if request.data.get("status") == "cancelled":

            # ===============================
            # ✅ ROLE CHECK
            # ===============================
            if request.user.role not in ["customer", "staffadmin"]:
                return Response(
                    {"status": False, "message": "Not allowed to cancel"},
                    status=status.HTTP_403_FORBIDDEN
                )
        
            # ===============================
            # ✅ SCHEDULE CHECK
            # ===============================
            if not service.schedule_date or not service.schedule_time:
                return Response(
                    {"status": False, "message": "Schedule not set"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
            scheduled_datetime = datetime.combine(
                service.schedule_date,
                service.schedule_time
            )
        
            now = datetime.now()
        
            if now > scheduled_datetime - timedelta(hours=1):
                return Response(
                    {"status": False, "message": "Cannot cancel within 1 hour of schedule"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
            # ===============================
            # ✅ HANDLE MULTIPLE VENDOR IDS
            # ===============================
            vendor_ids_to_cancel = request.data.get("vendor_unique_id", [])
        
            if isinstance(vendor_ids_to_cancel, str):
                vendor_ids_to_cancel = [vendor_ids_to_cancel]
        
            # ===============================
            # ✅ IF NO ASSIGNMENTS → DIRECT CANCEL
            # ===============================
            if not service.assignments:
                service.status = "cancelled"
                service.save()
        
                serializer = ServiceRequestByUserSerializer(service)
                return Response(
                    {"status": True, "data": serializer.data},
                    status=status.HTTP_200_OK
                )
        
            # ===============================
            # ✅ UPDATE ASSIGNMENTS
            # ===============================
            updated_assignments = []
            cancelled_vendor_ids = []
        
            for entry in service.assignments:
                vendor_unique_id = entry[1]
                current_status = entry[3]
        
                if vendor_unique_id in vendor_ids_to_cancel and current_status != "cancelled":
                    entry[3] = "cancelled"
                    cancelled_vendor_ids.append(vendor_unique_id)
        
                updated_assignments.append(entry)
        
            service.assignments = updated_assignments
        
          
            if cancelled_vendor_ids:

                cancelled_vendors = AllLog.objects.filter(
                    unique_id__in=cancelled_vendor_ids,
                    role="vendor"
                )
            
                message = f"Service Request {service.request_id} has been cancelled. Regards-ICDS Technical"
                encoded_message = quote(message)
            
                for vendor in cancelled_vendors:
                    if vendor.phone:
            
                        url = (
                            f"http://bulksms.saakshisoftware.com/api/mt/SendSMS"
                            f"?user=Brainrock"
                            f"&password=123456"
                            f"&senderid=BCSINF"
                            f"&channel=trans"
                            f"&DCS=0"
                            f"&flashsms=0"
                            f"&number=9058423148"   # use real vendor phone
                            f"&text={encoded_message}"
                            f"&route=04"
                            f"&DLTTemplateId=1207163827265054435"
                            f"&PEID=1201163222226675668"
                        )
            
                        try:
                            response = requests.get(url,  timeout=100000)
            
                            print("SMS Response:", response.status_code, response.text)
            
                            if response.status_code != 200:
                                print("SMS failed for:", vendor.phone)
            
                        except Exception as e:
                            print("SMS sending failed:", str(e)) # prevent crash if SMS fails
        
            # ===============================
            # ✅ FINAL STATUS CHECK
            # ===============================
            if service.assignments:

                all_cancelled = all(entry[3] == "cancelled" for entry in service.assignments)
                all_completed = all(entry[3] == "completed" for entry in service.assignments)
            
                if all_completed:
                    service.status = "completed"
            
                elif all_cancelled:
                    service.status = "cancelled"
            
                else:
                    service.status = "assigned"
            
            else:
                service.status = "cancelled"
                # ✅ VENDOR STATUS UPDATE LOGIC
        if request.user.role == "vendor":

            vendor_unique_id = request.data.get("vendor_unique_id")
            new_status = request.data.get("status")

            if not vendor_unique_id or not new_status:
                return Response(
                    {"status": False, "message": "vendor_unique_id and status required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            updated = False

            for entry in service.assignments:
                # entry format:
                # [services_list, vendor_unique_id, vendor_name, status]
                if entry[1] == vendor_unique_id:
                    entry[3] = new_status
                    updated = True
                    break

            if not updated:
                return Response(
                    {"status": False, "message": "Vendor not assigned to this request"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        
            completed_services = []
            cancelled_services = []

           
            for entry in service.assignments:
                services_list = entry[0]     # list of services
                vendor_status = entry[3]

                if vendor_status == "completed":
                    completed_services.extend(services_list)

                elif vendor_status == "cancelled":
                    cancelled_services.extend(services_list)

           
            closed_services = set(completed_services) | set(cancelled_services)

          
            all_services_closed = all(
                req_service in closed_services
                for req_service in service.request_for_services
            )

            if all_services_closed:
                service.status = "completed"
            else:
                service.status = "assigned"

            service.save()

            return Response(
                {"status": True, "message": "Assignment status updated successfully"},
                status=status.HTTP_200_OK
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

    @transaction.atomic
    def post(self, request):
        request_id = request.data.get("request_id")
        assignments_payload = request.data.get("assignments")

        if not request_id or not assignments_payload:
            return Response(
                {"status": False, "message": "request_id and assignments required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            service_request = ServiceRequestByUser.objects.get(request_id=request_id)
        except ServiceRequestByUser.DoesNotExist:
            return Response(
                {"status": False, "message": "Request not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if not isinstance(assignments_payload, list):
            return Response(
                {"status": False, "message": "assignments must be a list"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not service_request.assignments:
            service_request.assignments = []

        for assignment in assignments_payload:
            vendor_unique_id = assignment.get("vendor_unique_id")
            service_list = assignment.get("request_for_services")

            if not vendor_unique_id or not isinstance(service_list, list):
                continue

            # Validate Vendor
            try:
                vendor_alllog = AllLog.objects.get(unique_id=vendor_unique_id, role="vendor")
                vendor_obj = Vendor.objects.get(unique_id=vendor_unique_id)
            except (AllLog.DoesNotExist, Vendor.DoesNotExist):
                continue

            # Prevent duplicate vendor assignment
            already_exists = any(
                vendor_unique_id == entry[1]
                for entry in service_request.assignments
            )

            if already_exists:
                continue

            # ✅ EXACT STRUCTURE:
            # [[services_list], vendor_unique_id, vendor_name]
            new_entry = [
                service_list,
                vendor_unique_id,
                vendor_obj.username,
                "assigned",
                 vendor_obj.mobile_number
            ]

            service_request.assignments.append(new_entry)

        service_request.status = "assigned"
        service_request.save()

        return Response(
            {"status": True, "message": "Vendors assigned successfully"},
            status=status.HTTP_200_OK
        )

@api_view(['GET'])
def get_services_categories(request):

    # Fetch only accepted records
    services = ServiceCategory.objects.filter(status='published')

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
    vendors = Vendor.objects.filter(is_active=True).values('unique_id','username','address','category')

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
            issues = StaffIssue.objects.all().order_by("-created_at")

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

        # 🔹 Check id exists in body
        if not issue_id:
            return Response(
                {"status": False, "message": "id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 🔹 Convert id safely to int
        try:
            issue_id = int(issue_id)
        except ValueError:
            return Response(
                {"status": False, "message": "Invalid id"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 🔹 Fetch issue
        try:
            issue = StaffIssue.objects.get(id=issue_id)
        except StaffIssue.DoesNotExist:
            return Response(
                {"status": False, "message": "Issue not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 🔹 Update using same serializer
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
class DistrictBlockAPIView(APIView):

    def get(self, request):
        district = request.query_params.get('district', '').strip()
        queryset = DistrictBlock.objects.all()
        if district:
            blocks = list(
                queryset.filter(district__iexact=district)
                        .order_by('block')
                        .values_list('block', flat=True)
            )

            if not blocks:
                return Response(
                    {"status": False, "message": "No blocks found for this district"},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response(
                {
                    "status": True,
                    "data": {
                        "state": "Uttarakhand",
                        "district": district.title(),
                        "blocks": blocks
                    }
                },
                status=status.HTTP_200_OK
            )
        districts = queryset.order_by('district', 'block') \
                            .values('district', 'block')

        result = {}
        for item in districts:
            result.setdefault(item['district'], []).append(item['block'])

        response_data = [
            {"district": d, "blocks": b}
            for d, b in result.items()
        ]

        return Response(
            {
                "status": True,
                "data": {
                    "state": "Uttarakhand",
                    "districts": response_data
                }
            },
            status=status.HTTP_200_OK
        )

class BillingAPIView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        elif self.request.method == "POST":
            return [IsStaffAdminFromAllLog()]
        elif self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsAdminFromAllLog()]
        return []

    def get(self, request):
        bill_id = request.query_params.get("bill_id")
        vendor_id = request.query_params.get("vendor_id")

        # If bill_id is provided → return single bill
        if bill_id:
            try:
                bill = Billing.objects.get(bill_id=bill_id)
                serializer = BillingSerializer(bill)
                return Response(
                    {"status": True, "data": serializer.data},
                    status=status.HTTP_200_OK
                )
            except Billing.DoesNotExist:
                return Response(
                    {"status": False, "message": "Bill not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Otherwise filter queryset
        bills = Billing.objects.all().order_by("-created_at")

        if vendor_id:
            bills = bills.filter(vendor_id=vendor_id)

        serializer = BillingSerializer(bills, many=True)

        return Response(
            {
                "status": True,
                "data": serializer.data,
                "count": bills.count()
            },
            status=status.HTTP_200_OK
        )
    def post(self, request):
        serializer = BillingSerializer(data=request.data)

        if serializer.is_valid():
            bill = serializer.save()

            # Generate PDF after saving
            generate_bill_pdf(bill)

            return Response(
                {"status": True, "message": "Bill created successfully"},
                status=status.HTTP_201_CREATED
            )

        return Response(
            {"status": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )


    def put(self, request):
        bill_id = request.data.get("bill_id")

        if not bill_id:
            return Response(
                {"status": False, "message": "bill_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            bill = Billing.objects.get(bill_id=bill_id)
        except Billing.DoesNotExist:
            return Response(
                {"status": False, "message": "Bill not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = BillingSerializer(bill, data=request.data, partial=True)

        if serializer.is_valid():
            bill = serializer.save()
            generate_bill_pdf(bill)  # regenerate PDF

            return Response(
                {"status": True, "message": "Bill updated successfully"},
                status=status.HTTP_200_OK
            )

        return Response(
            {"status": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

   
    def delete(self, request):
        bill_id = request.data.get("bill_id")

        if not bill_id:
            return Response(
                {"status": False, "message": "bill_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            bill = Billing.objects.get(bill_id=bill_id)
            bill.delete()
            return Response(
                {"status": True, "message": "Bill deleted successfully"},
                status=status.HTTP_200_OK
            )
        except Billing.DoesNotExist:
            return Response(
                {"status": False, "message": "Bill not found"},
                status=status.HTTP_404_NOT_FOUND
            )
class ContactUsAPIView(APIView):
    
    permission_classes = [IsAuthenticated]
    def get_permissions(self):
        if self.request.method == "POST":
            return [AllowAny()]
        return [IsAdminFromAllLog()]
    
    def post(self, request):
        serializer = ContactUsSerializer(data=request.data)
        if serializer.is_valid():
            contact = serializer.save()
            return Response(
                {"message": "Contact message submitted successfully!"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def get(self, request):
        contacts = ContactUs.objects.all().order_by('-id')
        serializer = ContactUsSerializer(contacts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
class SolarInstallationQueryAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == "POST":
            return [AllowAny()]
        return [IsAdminFromAllLog()]

    # Create Query
    def post(self, request):
        serializer = SolarInstallationQuerySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Solar installation query submitted successfully!"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # List All Queries (Admin Only)
    def get(self, request):
        queries = SolarInstallationQuery.objects.all().order_by('-id')
        serializer = SolarInstallationQuerySerializer(queries, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Delete Query (Admin Only)
    def delete(self, request):
        query_id = request.data.get("id")

        if not query_id:
            return Response(
                {"error": "Query ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            query = SolarInstallationQuery.objects.get(id=query_id)
        except SolarInstallationQuery.DoesNotExist:
            return Response(
                {"error": "Query not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        query.delete()
        return Response(
            {"message": "Query deleted successfully"},
            status=status.HTTP_200_OK
        )
        
        
class CompanyDetailsItemAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAdminFromAllLog()]


    def post(self, request):
        serializer = CompanyDetailsItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Company details item created successfully!"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def get(self, request):
        items = CompanyDetailsItem.objects.all().order_by('-id')
        serializer = CompanyDetailsItemSerializer(items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Update (Using request.data.get("id"))
    def put(self, request):
        item_id = request.data.get("id")

        if not item_id:
            return Response(
                {"error": "Item ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            item = CompanyDetailsItem.objects.get(id=item_id)
        except CompanyDetailsItem.DoesNotExist:
            return Response(
                {"error": "Item not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CompanyDetailsItemSerializer(item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Company details item updated successfully!"},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Delete (Using request.data.get("id"))
    def delete(self, request):
        item_id = request.data.get("id")

        if not item_id:
            return Response(
                {"error": "Item ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            item = CompanyDetailsItem.objects.get(id=item_id)
        except CompanyDetailsItem.DoesNotExist:
            return Response(
                {"error": "Item not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        item.delete()
        return Response(
            {"message": "Company details item deleted successfully!"},
            status=status.HTTP_204_NO_CONTENT
        )
        
class SendOTP(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        phone = request.data.get('phone')

        if not phone or not phone.isdigit():
            return Response({"success": False, "message": "Valid phone number required"}, status=400)

        # Generate OTP
        
        otp = str(random.randint(100000, 999999))
        message = f"Your onetime OTP is {otp} Regards-ICDS Technical"
        encoded_message = quote(message)  # URL encode the message

        # Build the URL (like PHP curl)
        url = (
            f"http://bulksms.saakshisoftware.com/api/mt/SendSMS"
            f"?user=Brainrock"
            f"&password=123456"
            f"&senderid=BCSINF"
            f"&channel=trans"
            f"&DCS=0"
            f"&flashsms=0"
            f"&number={phone}"
            f"&text={encoded_message}"
            f"&route=04"
            f"&DLTTemplateId=1207163827265054435"
            f"&PEID=1201163222226675668"
        )

        try:
            response = requests.get(url, timeout=100000)

            if response.status_code == 200:
                # Save OTP to DB
                try:
                    otp_entry = PhoneOTP.objects.get(phone_number=phone)
                    otp_entry.otp_code = otp
                    otp_entry.created_at = timezone.now()
                    otp_entry.is_verified = False
                    otp_entry.save()
                except PhoneOTP.DoesNotExist:
                    PhoneOTP.objects.create(
                        phone_number=phone,
                        otp_code=otp,
                        is_verified=False,
                        created_at=timezone.now()
                    )

                return Response({"success": True, "message": "OTP sent successfully"},  status=status.HTTP_200_OK)

            else:
                return Response({"success": False, "message": "SMS gateway error"}, status=500)

        except Exception as e:
            print("OTP sending failed:", str(e))
            return Response({"success": False, "message": "OTP sending failed (network error)"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class VerifyOTP(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        phone = request.data.get('phone')
        otp = request.data.get('otp')

        if not phone or not otp:
            return Response({"success": False, "message": "Phone and OTP are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otp_entry = PhoneOTP.objects.get(phone_number=phone)

            if otp_entry.otp_code == otp:
                otp_entry.is_verified = True
                otp_entry.save()
                # Also update AllLog.verified for this phone number (ensure update is committed)
               
                return Response({"success": True, "message": "OTP verified successfully"}, status=status.HTTP_200_OK)
            else:
                return Response({"success": False, "message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        except PhoneOTP.DoesNotExist:
            return Response({"success": False, "message": "Phone number not found"}, status=status.HTTP_404_NOT_FOUND)
        
class ResetPassword(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        phone = request.data.get("phone")
        role = request.data.get("role")
        new_password = request.data.get("new_password")

        if not phone or not role or not new_password:
            return Response(
                {"success": False, "message": "Phone, role and new password required"},
                status=400
            )

        try:
            otp_entry = PhoneOTP.objects.get(phone_number=phone)

            if not otp_entry.is_verified:
                return Response(
                    {"success": False, "message": "OTP not verified"},
                    status=400
                )

            user = AllLog.objects.get(phone=phone, role=role)

      
            user.password = make_password(new_password)
            user.save()

          
            otp_entry.is_verified = False
            otp_entry.save()

            return Response(
                {"success": True, "message": "Password reset successfully"},
                status=status.HTTP_200_OK
            )

        except PhoneOTP.DoesNotExist:
            return Response(
                {"success": False, "message": "OTP not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        except AllLog.DoesNotExist:
            return Response(
                {"success": False, "message": "User not found"},
                 status=status.HTTP_404_NOT_FOUND
            )