from django.shortcuts import render,redirect
from staff.models import Restaurant,User
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login as auth_login
from django.utils import timezone
import random,time



# Create your views here.
def management_login(request):
    if request.method=="POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        print(username)
        print(password)
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            # ✅ If superuser, go to Django admin
            if user.is_superuser:
                return redirect('/admin/')
            owner = user.owner_profile 
            restaurant = Restaurant.objects.filter(owner=owner).first()
            return redirect('management-home',restaurant.id)  # redirect to dashboard after login
        else:
            messages.error(request, "Invalid username or password.")
    return render(request,"login.html")


# Step 1: Email submission to start password reset
def forget_password(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = User.objects.get(email=email)
            otp = str(random.randint(100000, 999999))
            request.session['reset_email'] = email
            request.session['reset_otp'] = otp
            # TODO: Send OTP via email
            print(f"[DEBUG] OTP sent to {email}: {otp}")
            return redirect('verify-otp')
        except User.DoesNotExist:
            messages.error(request, "No account found with this email.")
    return render(request, "forgot_password.html")


# Step 2: OTP Verification
def verify_otp(request):
    # Restrict access if email is not verified (no session)
    if 'reset_email' not in request.session or 'reset_otp' not in request.session:
        return redirect('forgot-password')
    
    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        session_otp = request.session.get('reset_otp')
        if entered_otp == session_otp:
            request.session['otp_verified'] = True
            return redirect('reset-password')
        else:
            messages.error(request, "Invalid OTP.")
    return render(request, "verify_otp.html")


# Step 3: Set new password
def reset_password(request):
    # Restrict access unless OTP is verified
    if not request.session.get('otp_verified') or 'reset_email' not in request.session:
        return redirect('forgot-password')

    if request.method == "POST":
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
        elif len(new_password) < 6:
            messages.error(request, "Password should be at least 6 characters.")
        else:
            try:
                email = request.session.get('reset_email')
                user = User.objects.get(email=email)

                user.password = make_password(new_password)
                user.save()

                messages.success(request, "Password reset successful.")
                
                # Clear session
                for key in ['reset_email', 'reset_otp', 'otp_verified']:
                    if key in request.session:
                        del request.session[key]
                return redirect('management-login')
            except User.DoesNotExist:
                messages.error(request, "Something went wrong.")
                return redirect('forgot-password')

    return render(request, "reset_password.html")
