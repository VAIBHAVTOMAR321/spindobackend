# urls.py

from django.urls import path
from .views import AssignVendorAPIView, CustomerIssueView, CustomerRegistrationView,CustomTokenRefreshView, LoginView, ServiceRequestAPIView, StaffAdminRegistrationView, VendorRegistrationView, ServiceCategoryView, VendorRequestView, get_all_vendors, get_categories
urlpatterns = [

    path('customer/register/', CustomerRegistrationView.as_view()),  # Supports GET with ?unique_id=USER-001
    path('staffadmin/register/', StaffAdminRegistrationView.as_view()),
    path('vendor/register/', VendorRegistrationView.as_view()),
    path('service-category/', ServiceCategoryView.as_view()),
    path('token/refresh/', CustomTokenRefreshView.as_view()),
    path('vendor/request/', VendorRequestView.as_view()),
    path('login/', LoginView.as_view()),
    path('customer/issue/', CustomerIssueView.as_view(), name='customer-issue'),
    path('customer/requestservices/', ServiceRequestAPIView.as_view(), name='customer-requestservices'),
    path('assign-vendor/', AssignVendorAPIView.as_view(), name='assign-vendor'),
    path('get-categories/', get_categories, name='get_categories'),
    path('vendor/list/', get_all_vendors, name='get_all_vendors'),

]
