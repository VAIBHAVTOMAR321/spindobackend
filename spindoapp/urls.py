# urls.py

from django.urls import path
from .views import CustomerRegistrationView, LoginView, StaffAdminRegistrationView

urlpatterns = [

    path('customer/register/', CustomerRegistrationView.as_view()),
    path('staffadmin/register/', StaffAdminRegistrationView.as_view()),

    path('login/', LoginView.as_view()),

]
