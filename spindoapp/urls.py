# urls.py

from django.urls import path
from .views import CustomerRegistrationView, LoginView, StaffAdminRegistrationView, VendorRegistrationView

urlpatterns = [

    path('customer/register/', CustomerRegistrationView.as_view()),  # Supports GET with ?unique_id=USER-001
    path('staffadmin/register/', StaffAdminRegistrationView.as_view()),
    path('vendor/register/', VendorRegistrationView.as_view()),
    path('login/', LoginView.as_view()),

]
