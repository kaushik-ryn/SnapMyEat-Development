"""
URL configuration for SnapMyEat project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from customer import views as customer_views
from staff import views as staff_views
from . import views
from . import settings
from django.conf.urls.static import static

urlpatterns = [
    path('<str:restaurantID>/<int:tableNo>/',include("customer.urls")),
    path('<str:restaurantID>/management/',include("staff.urls")),

    path("login/", views.management_login, name="management-login"),

    path("forget/password/", views.forget_password, name="forgot-password"),
    path("forget/password/verify/otp", views.verify_otp, name="verify-otp"),
    path("reset/password", views.reset_password, name="reset-password"),

    path("get-cart-details/<str:restaurantID>/", customer_views.fetch_details, name="fetch_details"),  # New API route
    path("waiter-call/<str:restaurantID>/",customer_views.call_waiter_socket,name="waiter_call"),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
