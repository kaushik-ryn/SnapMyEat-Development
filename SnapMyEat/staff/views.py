from django.shortcuts import render,redirect,HttpResponse
from django.http import JsonResponse
from datetime import timedelta,datetime
from django.utils import timezone
from django.db.models import Sum,Prefetch
from collections import Counter
from .models import Order,Restaurant,MenuItem,Table,ItemTag,MenuItemSize,MenuCategory
from django.contrib import messages
from io import BytesIO
from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from customer.utils import verify_restaurant_ownership
import uuid,json,random,qrcode,os,re

DESCRIPTION_POOL = [
    # Indian
    "Authentic Indian flavors with spices that warm your soul.",
    "Rich curries and classic Indian dishes made fresh daily.",
    "Celebrate India’s culinary heritage on a single plate.",
    "Aromatic, spicy, and deeply satisfying Indian creations.",
    "Traditional recipes passed down through generations.",

    # Chinese / Asian
    "Wok-tossed noodles, dumplings, and savory stir-fries await.",
    "Bold Asian flavors crafted with fresh ingredients and flair.",
    "From sweet soy to spicy Szechuan, flavor-packed Chinese delights.",
    "A mix of crunch, spice, and umami in every bite.",
    "Perfect balance of sweet, sour, and savory Chinese dishes.",

    # Western / Continental
    "Grilled, baked, and seasoned to perfection – Western favorites.",
    "Classic comfort food from global cuisines, reimagined.",
    "Creamy pastas, juicy steaks, and fresh salads await.",
    "A wholesome mix of flavors inspired by the West.",
    "Perfect for fans of continental flair and flavor.",

    # Street Food / Snacks
    "Street-style snacks packed with punch and personality.",
    "Perfect for sharing, snacking, or satisfying quick cravings.",
    "Crispy, cheesy, spicy – snack-time hits you’ll love.",
    "Fast, flavorful, and fun — your street food fix.",
    "Chaat, rolls, and fried treats made to perfection.",

    # Beverages / Desserts
    "Cool off with refreshing drinks and sweet indulgences.",
    "Treat yourself to chilled beverages and dreamy desserts.",
    "From shakes to sweets — your sugar fix is here.",
    "Every sip and bite crafted to satisfy your cravings.",
    "Sweet, creamy, or fizzy — we’ve got it all!",

    # Drinks
    "Refreshing sips to cool you down anytime, anywhere.",
    "Fizz, fruit, and freshness in every glass.",
    "Chilled, tangy, and crafted for instant refreshment.",
    "Perfect blends to energize your mood.",
    "Smoothies, sodas, and everything in between.",
    "Sweet or strong—there’s a drink for everyone.",
    "Quench your thirst with bold, bubbly choices.",
    "Delightful drinks to complete every meal.",

    # Fusion / Chef Specials / Custom
    "Flavors collide in this chef-curated fusion masterpiece.",
    "Handpicked dishes that tell a unique culinary story.",
    "Where global flavors meet creative culinary twists.",
    "From traditional roots to experimental favorites.",
    "Crafted with flair — perfect for curious foodies.",

    # General / Reusable
    "Fresh ingredients, bold flavors, and made-to-order magic.",
    "A medley of signature creations, each worth a try.",
    "Tried, tested, and totally irresistible dishes.",
    "From starters to mains — every plate is a winner.",
    "Savory, satisfying, and full of culinary charm.",
    "Made with passion and plated with perfection.",
    "Feel-good food that hits the spot every time.",
    "Perfect pairings and standalone stars in every bite.",
    "Your new favorites — waiting to be discovered.",
    "A flavorful journey you’ll want to revisit often.",

    # Pasta
    "Rich, creamy, and saucy pasta creations made with love.",
    "A bite of Italy in every twirl.",
    "Wholesome pasta loaded with flavor and flair.",
    "Delightfully cheesy and cooked to perfection.",
    "Fresh herbs and hearty sauces on soft pasta.",
    "Pasta dishes that satisfy every craving.",
    "Savor Italian-style classics with every forkful.",
    "Where al dente meets absolute delight.",

    # Junk Food
    "Guilty pleasures, generously served.",
    "Loaded bites for when cravings strike hard.",
    "Fast, flavorful, and downright addictive.",
    "Perfect for cheat days and happy moods.",
    "Crispy, cheesy, saucy—snack dreams come true.",
    "Bold street-style flavors done right.",
    "Your favorite guilty snacks, all in one place.",
    "Satisfy your junk food obsession, deliciously.",

    # Pizza
    "Oven-fresh pizzas topped with love and cheese.",
    "From classic Margherita to cheesy overloads.",
    "Every slice oozes flavor and crunch.",
    "Perfectly baked crusts with irresistible toppings.",
    "Melty, cheesy, and endlessly satisfying.",
    "Get lost in the world of pizzas.",
    "A slice of joy in every bite.",
    "Thin crust, deep dish—pizzas for every mood.",

    # Burger
    "Stacked high with juicy goodness.",
    "Burgers that make your day better.",
    "Grilled to perfection, served with flair.",
    "Bold buns, loaded patties, epic flavors.",
    "Classic, cheesy, or spicy—choose your bite.",
    "Meaty, messy, and magnificently tasty.",
    "Bite-sized happiness between two buns.",
    "Craft burgers that go beyond ordinary.",

    # Others / General
    "Fresh picks that don’t fit a box but hit the spot.",
    "A flavorful surprise in every bite.",
    "Chef’s specials from various inspirations.",
    "Unique creations made to impress.",
    "Curated combinations of global favorites.",
    "Fusion foods that break all rules.",
    "Taste journeys beyond expectations.",
    "Special picks you won’t find elsewhere.",
]




# Create your views here.

@login_required
@verify_restaurant_ownership
def management_logout(request,restaurantID):
    logout(request)
    return redirect('management-login')


def upgrade(request,restaurantID):
    restaurantInstance = Restaurant.objects.get(id=restaurantID)
    return render(request,"staff/upgrade.html",{"restID":restaurantID,"restInstance":restaurantInstance})

@login_required
@verify_restaurant_ownership
def home(request,restaurantID):
    restaurantInstance = Restaurant.objects.get(id=restaurantID)
    return render(request,"staff/home.html",{"restID":restaurantID,"restInstance":restaurantInstance})


# ----------    ORDERS
@login_required
@verify_restaurant_ownership
def orders(request,restaurantID):
    restaurantInstance = Restaurant.objects.filter(id=restaurantID).first()
    query = request.GET.get("search","")
    status_filter = request.GET.get("status", "").strip().lower()

    orders = Order.objects.filter(restaurant=restaurantInstance)
    
    if query:
        query = query.lstrip("0")
        if query.isdigit():
            if len(query)>=3:
                orders = orders.filter(order_no=int(query))
            else:
                table_instance = Table.objects.filter(restaurant=restaurantInstance, table_number=int(query)).first()
                if table_instance:
                    orders = orders.filter(table=table_instance)
                else:
                    orders = Order.objects.none()
        else:
            orders = Order.objects.none()
    if status_filter in ["pending","preparing", "ready", "completed", "cancelled"]:
        orders = orders.filter(status=status_filter)
    context={
        "restID":restaurantID,"restInstance":restaurantInstance,
        "orders":orders.order_by("-created_at"),"query":query,
        "status_filter": status_filter
        }
    return render(request,"staff/order.html",context)


# ----------    UPDATE ORDER STATUS / AJAX 
@login_required
@verify_restaurant_ownership
def update_order_status(request,restaurantID):
    if request.method=="POST":
        try:
            data = json.loads(request.body)
            order_id = data.get("order_id")
            new_status = data.get("status")
            
            if order_id and new_status in ["pending","preparing", "ready", "completed", "cancelled"]:
                order = Order.objects.get(id=order_id)
                order.status = new_status
                order.save()
                return JsonResponse({"success": True, "new_status": new_status})
            else:
                return JsonResponse({"success": False, "error": "Invalid data"}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)


# ----------    SEE ALL ORDER
@login_required
@verify_restaurant_ownership
def see_orders(request,restaurantID):
    restaurantInstance = Restaurant.objects.filter(id=restaurantID).first()

    query = request.GET.get("search","")
    status_filter = request.GET.get("status", "").strip().lower()
    date_str = request.GET.get("date")

    # Default to yesterday
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = datetime.now().date() - timedelta(days=1)
    else:
        selected_date = datetime.now().date() - timedelta(days=1)

    orders = Order.objects.filter(restaurant=restaurantInstance,created_at__date=selected_date)
    # orders = Order.objects.filter(restaurant=restaurantInstance)
    
    if query:
        query = query.lstrip("0")
        if query.isdigit():
            if len(query)>=3:
                orders = orders.filter(order_no=int(query))
            else:
                table_instance = Table.objects.filter(restaurant=restaurantInstance, table_number=int(query)).first()
                if table_instance:
                    orders = orders.filter(table=table_instance)
                else:
                    orders = Order.objects.none()
        else:
            orders = Order.objects.none()
    if status_filter in ["preparing", "ready", "completed", "cancelled"]:
        orders = orders.filter(status=status_filter)
    context={
        "restID":restaurantID,"restInstance":restaurantInstance,
        "orders":orders.order_by("-created_at"),"query":query,
        "status_filter": status_filter,"selected_date": selected_date.strftime("%Y-%m-%d"),
        }
    return render(request,"staff/seeOrder.html",context)


# ----------    ITEMS
@login_required
@verify_restaurant_ownership
def menu_items(request,restaurantID):
    restaurantInstance = Restaurant.objects.filter(id=restaurantID).first()

    # Fetch search Term
    query = request.GET.get("search","")
    selected_tag = request.GET.get("tag", "").strip()

    menu_items = MenuItem.objects.filter(restaurant=restaurantInstance).select_related('category').prefetch_related('tags','item_sizes')  # item_sizes is the related_name in MenuItemSize
    all_tags = ItemTag.objects.filter(restaurant=restaurantInstance).all()

    if query:
        query = query.lstrip("0")
        if query.isdigit():
            menu_items = menu_items.filter(id=int(query))
        else:
            menu_items = menu_items.filter(name__icontains=query)

    # Apply tag filtering
    if selected_tag:
        if selected_tag == "__notag__":
            menu_items = menu_items.filter(tags__isnull=True)
        else:
            menu_items = menu_items.filter(tags__name=selected_tag)

    # Structure data for template rendering
    items_data = []
    for item in menu_items:
        items_data.append({
            "id": item.id,
            "name": item.name,
            "category": item.category.name,
            "is_available": item.is_available,
            "type": item.type,
            "tags": [tag.name for tag in item.tags.all()],
            # "tags": item.tags,
            "sizes": [
                {
                    "size": size.size,
                    "price": size.price,
                    "is_default": size.is_default
                }
                for size in item.item_sizes.all()
            ]
        })
    context = {
        "restID":restaurantID,"restInstance":restaurantInstance,
        "menu_items":items_data,"query":query,
        "all_tags":all_tags,"tag":selected_tag}
    return render(request,"staff/items.html",context)


@login_required
def menu_items_edit(request, restaurantID, itemID):
    restaurant = Restaurant.objects.get(id=restaurantID)
    item = MenuItem.objects.get(id=itemID)

    if request.method == "POST":
        item.name = request.POST.get("name")
        item.type = request.POST.get("type")
        item.is_available = True if request.POST.get("is_available") == "on" else False

        category_id = request.POST.get("category")
        if category_id:
            item.category = MenuCategory.objects.get(id=category_id)

        # Update image_url (fallback to default if empty or whitespace)
        image_url = request.POST.get("image_url", "").strip()
        if image_url:
            item.image_url = image_url
        else:
            item.image_url = "/static/images/staff/placeholder/default/1.jpg"

        # Save basic info
        item.save()

        # Tags update
        tag_ids = request.POST.getlist("tags")
        item.tags.set(tag_ids)

        # Sizes update — remove old ones, add new ones
        MenuItemSize.objects.filter(menu_item=item).delete()

        size_keys = [key for key in request.POST if key.startswith("size_")]
        default_index = request.POST.get("default_size")  # Example: ['2']
        if not default_index:
            messages.error(request, "Please select one size as default.")
            return redirect(request.path)
        for key in size_keys:
            index = key.split("_")[1]
            size_name = request.POST.get(f"size_{index}")
            price = request.POST.get(f"price_{index}")


            if size_name and price:
                MenuItemSize.objects.create(
                    menu_item=item,
                    size=size_name,
                    price=price,
                    is_default=(index == default_index)
                )

        # return redirect('management-menu', restaurantID=restaurantID)
        # At end of POST success
        return HttpResponse("<script>window.close();</script>")

    # On GET: send data to template
    categories = MenuCategory.objects.filter(restaurant=restaurant)
    tags = ItemTag.objects.filter(restaurant=restaurant)
    sizes = MenuItemSize.objects.filter(menu_item=item)
    types = ["Veg", "Non Veg"]  # Optional: customize as needed

    context = {
        "restID": restaurantID,
        "item": item,
        "categories": categories,
        "tags": tags,
        "selected_tags": item.tags.all(),
        "sizes": sizes,
        "types": types
    }
    return render(request, "staff/edit_item.html", context)


@login_required
@verify_restaurant_ownership
def menu_items_add(request,restaurantID):
    restaurant = Restaurant.objects.get(id=restaurantID)
    categories = MenuCategory.objects.filter(restaurant=restaurant)
    tags = ItemTag.objects.filter(restaurant=restaurant)

    if request.method == "POST":
        name = request.POST.get("name")
        category_id = request.POST.get("category")
        category = MenuCategory.objects.get(id=category_id)
        item_type =  request.POST.get("type")
        is_available = True if request.POST.get("is_available") == "on" else False
        image_url = request.POST.get('image_url', '').strip() or 'images/staff/placeholder/default/1.jpg'

        item = MenuItem.objects.create(
            restaurant=restaurant,
            category=category,
            name=name,
            type=item_type,
            is_available=is_available,
            image_url=image_url
        )

        # Handle Tags
        selected_tag_ids = request.POST.getlist("tags")
        tag_objs = ItemTag.objects.filter(id__in=selected_tag_ids, restaurant=restaurant)
        item.tags.set(tag_objs)

        # Handle Sizes
        size_keys = [key for key in request.POST if key.startswith("size_")]
        default_index = request.POST.get("default_size")  # Example: ['2']
        if not default_index:
            messages.error(request, "Please select one size as default.")
            return redirect(request.path)
        for key in size_keys:
            index = key.split("_")[1]
            size = request.POST.get(f"size_{index}")
            price = request.POST.get(f"price_{index}")
            if size and price:
                try:
                    price = float(price)
                    if size and price > 0:
                        MenuItemSize.objects.create(menu_item=item, size=size, price=price,is_default=(index == default_index))
                except (ValueError, TypeError):
                    continue  # Skip invalid price

        return redirect("management-menu-add", restaurantID)
        


    return render(request, "staff/add_item.html", {
        "restaurant": restaurant,
        "restID": restaurantID,
        "categories": categories,
        "tags": tags,
    })
    # return render(request,"staff/add_item.html",{"restID":restaurantID})


@login_required
def menu_items_del(request, restaurantID, itemID):
    if request.method == "POST":
        item = MenuItem.objects.filter(id=itemID, restaurant__id=restaurantID).first()
        if item:
            item.delete()
            return JsonResponse({"status": "success"}, status=200)
    return JsonResponse({"error": "Invalid request"}, status=400)


# ----------    ITEM IMAGE GENERATE - API
@login_required
@verify_restaurant_ownership
def get_image_by_name(request,restaurantID):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            name = data.get("name", "")
            name = re.sub(r'[^a-zA-Z0-9 ]+', '', name)  # clean up symbols
            keywords = name.split()
            # Try folder match for each keyword
            static_root = os.path.join(settings.BASE_DIR, "static", "images", "staff", "placeholder")
            all_folders = os.listdir(static_root)

            matched_folder = None

            # Try fuzzy/partial match with keywords against folder names
            for folder in all_folders:
                folder_lower = folder.lower()
                for keyword in keywords:
                    if keyword in folder_lower:
                        matched_folder = folder
                        break
                if matched_folder:
                    break

            if not matched_folder and "default" in keywords:
                if "default" in all_folders:
                    matched_folder = "default"

            if matched_folder:
                folder_path = os.path.join(static_root, matched_folder)
                image_files = [
                    f for f in os.listdir(folder_path)
                    if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
                ]

                if image_files:
                    selected_image = random.choice(image_files)
                    image_url = f"/static/images/staff/placeholder/{matched_folder}/{selected_image}"
                    print(image_url)
                else:
                    image_url = "/static/images/staff/placeholder/default/1.jpg"
            else:
                image_url = "/static/images/staff/placeholder/default/1.jpg"
            return JsonResponse({"image": image_url})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid method"}, status=405)


# ----------    CATEGORY
@login_required
@verify_restaurant_ownership
def menu_category(request, restaurantID):
    restaurantInstance = Restaurant.objects.filter(id=restaurantID).first()

    # Fetch search query
    query = request.GET.get("search", "").strip()

    # Get categories only for this restaurant
    categories = MenuCategory.objects.filter(restaurant=restaurantInstance)

    if query:
        query = query.lstrip("0")
        if query.isdigit():
            categories = categories.filter(id=int(query))
        else:
            categories = categories.filter(name__icontains=query)

    # Prefetch related menu items for each category
    categories = categories.prefetch_related(
        Prefetch(
            'category_items',
            queryset=MenuItem.objects.filter(restaurant=restaurantInstance).select_related('category')
            .prefetch_related('item_sizes', 'tags')
            .order_by('id'),to_attr='items_list'
        )
    )

    # Build structured data
    categorized_items = {}
    for category in categories:
        key = f"{category.id:03d}__{category.name}"
        categorized_items[key] = {
            "category_id": category.id,
            "category_name": category.name,
            "items": [
                {
                    "id": f"{item.id:03d}",
                    "name": item.name,
                    "type": item.type
                }
                for item in category.items_list
            ]
        }
    context= {
        "restID": restaurantID,"restInstance":restaurantInstance,
        "categorized_items": categorized_items,"query": query
        }
    return render(request, "staff/categories.html",context)


@login_required
def menu_category_edit(request,restaurantID,categoryID):
    category = MenuCategory.objects.get(id=categoryID)

    if request.method == "POST":
        # Update category fields
        name = request.POST.get("name", category.name)
        description  = request.POST.get("description", category.description)
        
        # Enforce word limit (e.g., 20 words max)
        word_limit = 20
        description_word_count = len(description.strip().split())

        # Only update if within limit
        if description_word_count <= word_limit:
            category.name = name
            category.description = description

        # if 'image' in request.FILES:
        #     category.image = request.FILES['image']
        
        category.save()
        # return redirect('management-category', restaurantID=restaurantID)
        # At end of POST success
        return HttpResponse("<script>window.close();</script>")
    
    # Get all items under this category
    items = MenuItem.objects.filter(category=category)

    # Simple search by name
    search_query = request.GET.get('itemSearch', '')
    if search_query:
        search_query = search_query.lstrip("0")
        items = items.filter(name__icontains=search_query) | items.filter(id__icontains=search_query)
    
    context = {
        "restID": restaurantID,
        "category": category,
        "items": items,
    }

    return render(request, "staff/edit_category.html", context)


@login_required
@verify_restaurant_ownership
def menu_category_add(request,restaurantID):
    restaurant = Restaurant.objects.get(id=restaurantID)
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()

        if name:
            category = MenuCategory.objects.create(
                restaurant=restaurant,
                name=name,
                description=description,
            )
            return redirect('management-category-add',restaurantID=restaurantID)  # Redirect to the menu list after adding

    return render(request, "staff/add_category.html", {"restID": restaurantID})


@login_required
@verify_restaurant_ownership
def menu_category_del(request, restaurantID, categoryID):
    if request.method == "POST":
        category = MenuCategory.objects.filter(id=categoryID, restaurant__id=restaurantID).first()
        if not category:
            return JsonResponse({"status": "error", "message": "Category not found."})

        item_count = category.category_items.count()
        if item_count > 0:
            return JsonResponse({
                "status": "error",
                "message": f"This category contains {item_count} item(s) and cannot be deleted."
            })

        category.delete()
        return JsonResponse({"status": "success"})

    return JsonResponse({"status": "error", "message": "Invalid request method."})

# ----------   API OF CATEGORY DESCRIPTION
@login_required
def generate_category_description(request, restaurantID):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        body = json.loads(request.body)
        name = body.get("name", "").strip().lower()
        name = re.sub(r'[^a-zA-Z0-9 ]+', '', name)  # clean up symbols
    except Exception:
        return JsonResponse({"error": "Invalid data"}, status=400)

    if not name:
        return JsonResponse({"error": "Category name required"}, status=400)

    # Split category name into words
    keywords = name.split()

    # Try to find matching descriptions based on any keyword
    matches = []
    for desc in DESCRIPTION_POOL:
        lowered = desc.lower()
        if any(word in lowered for word in keywords):
            matches.append(desc)

    # Fallback to full pool if no matches found
    selected = random.choice(matches if matches else DESCRIPTION_POOL)

    return JsonResponse({"description": selected})



# ---------     Tags
@login_required
@verify_restaurant_ownership
def menu_tags(request,restaurantID):
    restaurant = Restaurant.objects.get(id=restaurantID)
    # ------    POST METHOD
    if request.method =="POST":
        tagName = request.POST.get("tag_name").strip()
        if tagName:
            ItemTag.objects.create(restaurant=restaurant,name=tagName)
            return redirect('management-tags', restaurantID=restaurantID)

    tags = ItemTag.objects.filter(restaurant=restaurant)
    context={
        "restID": restaurantID,"restInstance":restaurant, "tags":tags
        }
    return render(request, "staff/tags.html", context)


@login_required
def menu_tags_edit(request,restaurantID,tagID):
    if request.method == "POST":
        try:
            tag = ItemTag.objects.get(id=tagID, restaurant__id=restaurantID)
            data = json.loads(request.body)
            new_name = data.get("name", "").strip()

            if new_name:
                tag.name = new_name
                tag.save()

        except ItemTag.DoesNotExist:
            pass  # optionally handle not found
        except json.JSONDecodeError:
            pass  # optionally handle bad JSON

    return redirect('management-tags', restaurantID)


@login_required
def menu_tags_del(request,restaurantID,tagID):
    if request.method == "POST":
        tag = ItemTag.objects.get(id=tagID, restaurant__id=restaurantID)
        if tag:
            items_with_tag = MenuItem.objects.filter(tags=tag)
            for item in items_with_tag:
                item.tags.remove(tag)
            tag.delete()
            return JsonResponse({"status": "success"}, status=200)
    return JsonResponse({"error": "Invalid request"}, status=400)


# ----------    TABLE/QR
@login_required
@verify_restaurant_ownership
def table_qr(request,restaurantID):
    restaurantInstance = Restaurant.objects.filter(id=restaurantID).first()
    # Handle Add Table (POST)
    if request.method == "POST" and "table_number" in request.POST:
        table_number = int(request.POST.get("table_number", 0))
        if table_number < 1 or table_number > 99:
            return redirect("management-table", restaurantID=restaurantID)

        # Generate dummy QR (you can replace with actual QR generation)
        qr_code = str(uuid.uuid4())[:10]  # Temporary QR code

        Table.objects.create(
            restaurant=restaurantInstance,
            table_number=table_number, 
            qr_code=qr_code
        )
        return redirect('management-table', restaurantID=restaurantID)

    # Handle Remove Table (GET ?remove=table_id)
    table_to_remove = request.GET.get("remove")
    if table_to_remove:
        Table.objects.filter(id=table_to_remove, restaurant=restaurantInstance).delete()
        return redirect('management-table', restaurantID=restaurantID)

    tables = Table.objects.filter(restaurant=restaurantInstance).order_by("table_number")
    context = {
        "restID": restaurantID,
        "restInstance": restaurantInstance,
        "tables": tables,
    }
    return render(request, "staff/table_qr.html", context)

# ----------    QR CODE GENERATE FOR TABLES - API
@never_cache
@login_required
def generate_table_qr(request, restaurantID, table_number):
    host = request.get_host()
    scheme = request.scheme
    full_url = f"{scheme}://{host}/{restaurantID}/{table_number}/menu-items/"

    qr = qrcode.make(full_url)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    buffer.seek(0)

    return HttpResponse(buffer, content_type='image/png')


# ----------    INSIGHT
@login_required
@verify_restaurant_ownership
def insight(request,restaurantID):

    restaurantInstance = Restaurant.objects.filter(id=restaurantID).first()
    days  = int(request.GET.get("days",30))
    start_date = timezone.now() - timedelta(days=days)
    completed_orders = Order.objects.filter(
        restaurant=restaurantInstance,
        status='preparing',
        created_at__gte=start_date
    )

    # Summary Statistics
    total_orders = completed_orders.count()
    total_revenue = completed_orders.aggregate(total=Sum('grand_total'))['total'] or 0
    avg_order_value = total_revenue / total_orders if total_orders else 0

    # Top Ordered Items (flatten and count)
    item_counter = Counter()
    item_revenue = {}
    for order in completed_orders:
        items = order.items
        if isinstance(items, str):
            items = json.loads(items)

        for item in items:
            name = item.get('name')
            sizes = item.get('sizes', [])

            for size in sizes:
                price = float(size.get('price', 0))
                quantity = int(size.get('quantity', 1))

                item_counter[name] += quantity
                item_revenue[name] = item_revenue.get(name, 0) + price * quantity        
    # for order in completed_orders:
    #     for item in order.items:
    #         print(item)
    #         name = item.get('name')
    #         price = float(item.get('price', 0))
    #         print(price)
    #         print(type(price))
    #         quantity = int(item.get('quantity', 1))

    #         item_counter[name] += quantity
    #         item_revenue[name] = item_revenue.get(name, 0) + price * quantity

    top_items = sorted(item_counter.items(), key=lambda x: x[1], reverse=True)[:5]
    top_ordered_items = [
        {
            'name': name,
            'count': count,
            'revenue': f"{item_revenue.get(name, 0):.2f}"
        }
        for name, count in top_items
    ]

    # Frequently Ordered Pairs 
    pair_counter = Counter()
    
    for order in completed_orders:
        item_names = sorted([item['name'] for item in order.items])
        for i in range(len(item_names)):
            for j in range(i + 1, len(item_names)):
                pair = tuple(sorted((item_names[i], item_names[j])))
                pair_counter[pair] += 1
    frequent_pairs = [
        {
            'item1': pair[0],
            'item2': pair[1],
            'count': count
        }
        for pair, count in pair_counter.most_common(3)
    ]

    context = {
        "restID": restaurantID,
        "restInstance":restaurantInstance,
        "days": days,
        "total_orders": total_orders,
        "total_revenue": f"{total_revenue:.2f}",
        "avg_order_value": f"{avg_order_value:.2f}",
        "top_items": top_ordered_items,
        "frequent_pairs": frequent_pairs
    }

    return render(request, "staff/insights.html", context)
    # return render(request,"staff/insights.html",{"restID":restaurantID})


# ----------    PROFILE
@login_required
@verify_restaurant_ownership
def profile(request,restaurantID):
    restaurant = Restaurant.objects.get(id=restaurantID)
    if request.method == "POST" and "display_picture" in request.FILES:
        if restaurant.display_picture and os.path.basename(restaurant.display_picture.name) != "default_profilepicture.jpg":
            restaurant.display_picture.delete(save=False)

        # Save new
        restaurant.display_picture = request.FILES['display_picture']
        restaurant.save()

        return JsonResponse({"success": True, "new_image_url": restaurant.display_picture.url})
    
    template_names = {
        "starter": {
            "name": "Starter Classic",
            "description": "A fast and lightweight starter template for quick menus.",
        },
        "modern": {
            "name": "Modern Minimalist",
            "description": "A clean and elegant template focusing on readability and beautiful imagery.",
        }
    }
    
    context = {
        "restID": restaurantID,"restaurant": restaurant,
        "template_names":template_names,
        "selected_template":template_names.get(restaurant.template)
        }
    return render(request, "staff/profile.html", context)





