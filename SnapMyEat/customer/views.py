import json
import random
from django.shortcuts import redirect, render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from staff.models import Owner, Restaurant, MenuCategory, MenuItem, ItemTag, Table, Payment, Order, MenuItemSize
from .utils import secure_customer_access
from django.db.models import Subquery, OuterRef, DecimalField
from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@secure_customer_access
def menu_items(request, restaurantID, tableNo, restaurant_instance, table_instance):
    """
    Fetches menu items for a given restaurant and table, applying filters 
    based on category, price, availability, vegetarian options, and tags.
    """
    try:
        items = MenuItem.objects.filter(restaurant=restaurant_instance)
        tags = ItemTag.objects.filter(restaurant=restaurant_instance)
        category_three = MenuCategory.objects.filter(restaurant=restaurant_instance)[:3]
        # recommendation = items[:3]

        for tag in tags:
            random_index = random.randint(1, 4)
            tag.image_filename = f"images/starter/slideshow{random_index}.jpg"

        price = request.GET.get("price")
        availability = request.GET.get('availability')
        is_veg = request.GET.get("veg")
        category = request.GET.get("category")
        tags_fetch = request.GET.get("tags")
        dish_name = request.GET.get("dish_name")

        # Apply filters dynamically
        if category:
            category_object = MenuCategory.objects.filter(name=category,restaurant=restaurant_instance).first()
            items = items.filter(category=category_object)
        else:
            category = "All Items"

        if price is not None:
            default_price_subquery = MenuItemSize.objects.filter(
                menu_item=OuterRef('pk'),
                is_default=True
            ).values('price')[:1]

            items = items.annotate(default_price=Subquery(default_price_subquery, output_field=DecimalField()))
            items = items.filter(default_price__lte=price)
            # items = MenuItemSize.objects.filter(menu_item=items,is_default=True,price__lte=price)
            # items = items.filter(price__lte=price)
        if availability is not None:
            items = items.filter(is_available=availability.lower() == "true")
        if is_veg is not None:
            items = items.filter(is_vegetarian=is_veg.lower() == "true")
        if tags_fetch != "All" and tags_fetch is not None:
            items = items.filter(tags__name=tags_fetch).distinct()
            category = tags_fetch
        if dish_name:
            items = items.filter(name__icontains=dish_name)
            category = "All Items"

        context = {
            "RST": restaurant_instance, "TABLE": tableNo, "ITEMS": items, "CAT": category,"cat_three":category_three,
            "price": price, "availability": availability, "is_veg": is_veg, "tags": tags,"recommendation":items
        }
        return render(request, f"customer/{restaurant_instance.template}/index.html", context)
    except Exception as e:
        return render(request, "customer/error.html", {"restaurantID": restaurantID, "table": tableNo, "error": e})


@secure_customer_access
def menu_category(request, restaurantID, tableNo, restaurant_instance, table_instance):
    """
    Fetches menu categories for a given restaurant and renders them in the category template.
    """
    try:
        categories = MenuCategory.objects.filter(restaurant=restaurant_instance)
        for category in categories:
            random_index = random.randint(1, 4)
            category.image_filename = f"images/starter/category/{random_index}.jpg"

        return render(request, f"customer/{restaurant_instance.template}/category.html", {"RST": restaurant_instance, "TABLE": tableNo, "CAT": categories})
    except Exception as e:
        return render(request, "customer/error.html", {"restaurantID": restaurantID, "table": tableNo, "error": e})


@secure_customer_access
def placed_order(request, restaurantID, tableNo, restaurant_instance, table_instance):
    """
    Handles order placement, calculates total cost, and stores order details in the database.
    """
    try:
        if request.method == "POST":
            cart_items = request.POST.get("cartItems", "[]")
            final_order = json.loads(cart_items)
            grand_total = sum(size["quantity"] * size["price"] for item in final_order for size in item["sizes"])
            with transaction.atomic():
                # Lock existing orders to prevent duplicate order_no
                last_order = (
                    Order.objects.select_for_update()
                    .filter(restaurant=restaurant_instance)
                    .order_by("-order_no")
                    .first()
                )

                # Generate safe order number (loops back to 101 if needed)
                if last_order and last_order.order_no < 999:
                    next_order_no = last_order.order_no + 1
                else:
                    next_order_no = 101

                # Create the order with assigned safe order number
                order_instance = Order.objects.create(
                    restaurant=restaurant_instance,
                    table=table_instance,
                    items=final_order,
                    order_no=next_order_no,
                    status="pending",
                    grand_total=grand_total,  
                )
            # Send WebSocket update to staff
            print("order saved, about to be in channel")
            channel_layer = get_channel_layer()
            try:
                async_to_sync(channel_layer.group_send)(
                    f"restaurant_{restaurant_instance.id}_orders",  # Group name format
                    {
                        "type": "send_order_notification",
                        "order": {
                            "id":order_instance.id,
                            "order_no": order_instance.order_no,
                            "time": order_instance.created_at.strftime("%d %B %Y, %I:%M %p"),
                            # "time":order_instance.created_at,
                            "items": final_order,
                            "table": table_instance.table_number,
                            "total": grand_total,
                            "status":order_instance.status
                        },
                    }
                )
            except Exception as e:
                print(f"Error sending group message: {e}")
            print("channel done")

            return render(request, f"customer/{restaurant_instance.template}/placed_order.html", {"RST": restaurant_instance, "table": tableNo, "orderNo": order_instance.order_no})
        else:
            order_instance = Order.objects.filter(restaurant=restaurant_instance, table=table_instance).order_by("-created_at").first()
            return render(request, f"customer/{restaurant_instance.template}/placed_order.html", {"RST": restaurant_instance, "table": tableNo, "orderNo": order_instance.order_no})

    except Exception as e:
        return render(request, "customer/error.html", {"restaurantID": restaurantID, "table": tableNo, "error": e})


@secure_customer_access
def order_details(request, restaurantID, tableNo, restaurant_instance, table_instance):
    """
    Retrieves order details based on order number or the latest order for a table.
    """
    try:
        order_no = request.POST.get("OrderNumber") if request.method == "POST" else None
        order_instance = Order.objects.filter(restaurant=restaurant_instance, table=table_instance, order_no=order_no).first() if order_no else Order.objects.filter(restaurant=restaurant_instance, table=table_instance).order_by("-created_at").first()
        return render(request, f"customer/{restaurant_instance.template}/order_details.html", {"RST": restaurant_instance, "table": tableNo, "order_instance": order_instance})
    except Exception as e:
        return render(request, "customer/error.html", {"restaurantID": restaurantID, "table": tableNo, "error": e})


@secure_customer_access
def order_summary(request, restaurantID, tableNo, restaurant_instance, table_instance):
    """
    Renders the order summary page for the customer.
    """
    try:
        return render(request, f"customer/{restaurant_instance.template}/order_summary.html", {"RST": restaurant_instance, "table": tableNo})
    except Exception as e:
        return render(request, "customer/error.html", {"restaurantID": restaurantID, "table": tableNo, "error": e})


@secure_customer_access
def view_order(request, restaurantID, tableNo, restaurant_instance, table_instance):
    return render(request, f"customer/{restaurant_instance.template}/view_order.html", {"RST": restaurant_instance, "TABLE": tableNo})


# API ROUTE
def fetch_details(request, restaurantID):
    """
    Receives cart data from the frontend, retrieves item details, and returns updated cart information.
    """
    if request.method == "POST":
        try:
            cart_data = json.loads(request.body)
            final_cart = []

            for item in cart_data:
                menu_item = MenuItem.objects.filter(id=item["id"]).first()
                if not menu_item:
                    continue

                sizes_list = []
                for size_data in item["sizes"]:
                    size_entry = MenuItemSize.objects.filter(menu_item=menu_item, size=size_data["size"]).first()
                    if size_entry:
                        sizes_list.append({
                            "size": size_data["size"],
                            "quantity": size_data["quantity"],
                            "price": float(size_entry.price)
                        })
                
                final_cart.append({"id": menu_item.id, "name": menu_item.name, "sizes": sizes_list})
            
            return JsonResponse(final_cart, safe=False)
        
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=400)


# API TO CALL WAITER SOCKET
@csrf_exempt
def call_waiter_socket(request,restaurantID):
    if request.method != "POST":
        return JsonResponse({
            "ok": False,
            "error": "Invalid request method"
        }, status=405)
    try:
        data = json.loads(request.body)
        table_no = data.get("table")

        if not table_no:
            return JsonResponse({
                "ok": False,
                "error": "Missing 'table' in request data"
            }, status=400)

        # Send WebSocket message to waiter group
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"restaurant_{restaurantID}_waiter",
            {
                "type": "waiter_call",   # 👈 must match the method name in consumer
                "table": table_no
            }
        )

        return JsonResponse({
            "ok": True,"message": f"Waiter called for table {table_no}","table": table_no}, status=200)

    except Exception as e:
        return JsonResponse({"ok": False,"error": str(e)}, status=500)

