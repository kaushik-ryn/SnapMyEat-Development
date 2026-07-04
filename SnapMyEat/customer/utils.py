# from django.shortcuts import render
# from staff.models import Restaurant, Table

# def fetch_restaurant_and_table(view_func):
#     """
#     Decorator to fetch restaurant and table instances for a given restaurant ID and table number.
#     """
#     def wrapper(request, restaurantID, tableNo, *args, **kwargs):
#         try:
#             restaurant_instance = Restaurant.objects.filter(id=restaurantID).first()
#             table_instance = Table.objects.filter(restaurant=restaurant_instance, table_number=tableNo).first()

#             if not restaurant_instance:
#                 return render(request, "customer/error.html", {
#                     "restaurantID": restaurantID,
#                     "table": tableNo,
#                     "error": "Restaurant not found."
#                 })
            
#             kwargs["restaurant_instance"] = restaurant_instance
#             kwargs["table_instance"] = table_instance
#             return view_func(request, restaurantID, tableNo, *args, **kwargs)
        
#         except Exception as e:
#             return render(request, "customer/error.html", {
#                 "restaurantID": restaurantID,
#                 "table": tableNo,
#                 "error": str(e)
#             })
    
#     return wrapper



import time
from functools import wraps
from django.shortcuts import render,redirect
from django.http import HttpResponseForbidden
from staff.models import Restaurant, Table
from django.contrib.auth import logout

# ----------------------    C U S T O M E R  U R L  -  H A N D L I N G
# Cookie expiry time (in seconds) — 1 hour
COOKIE_EXPIRY = 60 * 2

def secure_customer_access(view_func):
    """
    Decorator to:
    1. Validate restaurant and table from DB.
    2. Set signed cookies on first access.
    3. Prevent tampering with URL params.
    4. Expire access after defined time.
    5. Pass restaurant/table instance to view.
    """
    @wraps(view_func)
    def wrapper(request, restaurantID, tableNo, *args, **kwargs):
        # Fetch from DB
        restaurant_instance = Restaurant.objects.filter(id=restaurantID).first()
        if not restaurant_instance:
            return render(request, "customer/error.html", {
                "restaurantID": restaurantID,
                "table": tableNo,
                "error": "Restaurant not found."
            })

        table_instance = Table.objects.filter(restaurant=restaurant_instance, table_number=tableNo).first()
        if not table_instance:
            return render(request, "customer/error.html", {
                "restaurantID": restaurantID,
                "table": tableNo,
                "error": "Table not found in this restaurant."
            })

        now = int(time.time())

        try:
            # 1. Read signed cookies from the user's browser.
            # These cookies were set earlier when the QR was first scanned.
            cookie_restaurantID = request.get_signed_cookie('restaurantID', salt='scanmyeat')
            cookie_tableNo = request.get_signed_cookie('tableNo', salt='scanmyeat')
            entry_time = int(request.get_signed_cookie('entryTime', salt='scanmyeat'))

            # ----------- Tampering detection
            # 2. Compare the cookie values with the current URL values.
            if cookie_restaurantID != restaurantID or str(cookie_tableNo) != str(tableNo):
                # If they don't match, it means the user tried to change the URL manually.
                return render(request, "customer/error.html", {
                    "restaurantID": restaurantID,
                    "table": tableNo,
                    "error": "URL tampering detected."
                })


            # Expired access
            # 3. Check if the access time has expired.
            if now - entry_time > COOKIE_EXPIRY:
                return render(request, "customer/error.html", {
                    "restaurantID": restaurantID,
                    "table": tableNo,
                    "error": "Access expired. Please rescan the QR code."
                })

        except KeyError:
            # First visit — set cookies
            # 4. If cookies are not set (first time visitor), we set them now.
            response = view_func(request, restaurantID, tableNo, restaurant_instance=restaurant_instance, table_instance=table_instance, *args, **kwargs)
            response.set_signed_cookie('restaurantID', restaurantID, salt='scanmyeat', max_age=COOKIE_EXPIRY)
            response.set_signed_cookie('tableNo', tableNo, salt='scanmyeat', max_age=COOKIE_EXPIRY)
            response.set_signed_cookie('entryTime', str(now), salt='scanmyeat', max_age=COOKIE_EXPIRY)
            return response

        # All checks passed — allow view with injected DB objects
        return view_func(request, restaurantID, tableNo, restaurant_instance=restaurant_instance, table_instance=table_instance, *args, **kwargs)

    return wrapper



# ----------------------    S T A F F  U R L -  H A N D L I N G
def verify_restaurant_ownership(view_func):
    """
    Verifies if the logged-in user owns the restaurant in the URL.
    Logs out and redirects to login if access is invalid or tampered.
    """
    @wraps(view_func)
    def wrapper(request, restaurantID, *args, **kwargs):
        user = request.user

        # 1. Must be logged in
        if not user.is_authenticated:
            return redirect("management-login")

        # If user is superuser, skip owner check and continue
        if user.is_superuser:
            restaurant = Restaurant.objects.filter(id=restaurantID).first()
        else:
            if not hasattr(user, "owner_profile"):
                logout(request)
                return redirect("management-login")

            # 2. Check if the restaurant belongs to the current user
            owner = user.owner_profile
            restaurant = Restaurant.objects.filter(id=restaurantID, owner=owner).first()
        
        if not restaurant:
            logout(request)  # Invalidate session
            return redirect("management-login")  # Redirect to login
        
        return view_func(request, restaurantID, *args, **kwargs)

    return wrapper
