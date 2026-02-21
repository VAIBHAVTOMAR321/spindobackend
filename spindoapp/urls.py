# urls.py

from django.urls import path
from .views import CustomerRegistrationView,BillingAPIView,ContactUsAPIView, LoginView, SolarInstallationQueryAPIView,StaffIssueAPIView, StaffAdminRegistrationView,get_all_vendors,DistrictBlockAPIView, VendorRegistrationView, get_services_categories, ServiceCategoryView,CustomTokenRefreshView,VendorRequestView,CustomerIssueAPIView,ServiceRequestAPIView,AssignVendorAPIView

urlpatterns = [

    path('customer/register/', CustomerRegistrationView.as_view()),  # Supports GET with ?unique_id=USER-001
    path('staffadmin/register/', StaffAdminRegistrationView.as_view()),
    path('vendor/register/', VendorRegistrationView.as_view()),
    path('service-category/', ServiceCategoryView.as_view()),
    path('token/refresh/', CustomTokenRefreshView.as_view()),
    path('vendor/request/', VendorRequestView.as_view()),
     path('customer/issue/', CustomerIssueAPIView.as_view(), name='customer-issue'),
    path('login/', LoginView.as_view()),
    path('customer/requestservices/', ServiceRequestAPIView.as_view(), name='customer-requestservices'),
    path('assign-vendor/', AssignVendorAPIView.as_view(), name='assign-vendor'),
    path('get-service/categories/',  get_services_categories, name='get_categories'),
    path('vendor/list/', get_all_vendors, name='get_all_vendors'),
    path('staffadmin/issue/', StaffIssueAPIView.as_view(), name='staff-issue'),
    path('district-blocks/', DistrictBlockAPIView.as_view(), name='district-blocks'),
    path("billing/", BillingAPIView.as_view(), name="billing-api"),
    path("contact-us/", ContactUsAPIView.as_view(), name="contact-us-api"),
    path('solar-query/', SolarInstallationQueryAPIView.as_view(),name="solar-query"),
]
