# urls.py

from django.urls import path
from .views import CustomerRegistrationView, LoginView

urlpatterns = [

    path('customer/register/', CustomerRegistrationView.as_view()),

    path('login/', LoginView.as_view()),

]
