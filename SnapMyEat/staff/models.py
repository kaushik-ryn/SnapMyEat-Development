from django.db import models,transaction
import uuid,os
from django.db.models import Max
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.files.storage import default_storage

# Utility function for generating unique short UUIDs (15 characters)
def generate_short_uuid():
    return str(uuid.uuid4().hex)[:15]  # Generates a 15-character unique ID

# -------- CUSTOM FUNCTION TO DYNAMICALLY SET UPLOAD PATH FOR RESTAURANT DP -------- #
def restaurant_dp_upload_path(instance, filename):
    """
    Generate a dynamic upload path for the restaurant display picture.
    - If instance.id exists: media/RST-DP/RST-001/RST-001.jpeg
    - Else (unsaved): media/temp.jpeg
    """
    ext = filename.split('.')[-1]
    filename = f"{instance.id}.{ext}" if instance.id else "temp.jpeg"
    return os.path.join("RST-DP",f"{instance.id}", filename)

# Owner Model
class Owner(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='owner_profile',null=True, blank=True)
    id = models.CharField(max_length=10, primary_key=True, editable=False)  # Custom formatted ID
    # name = models.CharField(default="Owner Name", max_length=200)
    # email = models.EmailField(max_length=150, unique=True, default="Email")
    phone_number = models.CharField(max_length=10, default="Phone Number")
    address = models.TextField(default="Address")

    # password = models.CharField(max_length=128,default="HELLO WORLD")
    is_active = models.BooleanField(default=True)

    # --- Dynamic Info from linked User ---
    @property
    def username(self):
        return self.user.username if self.user else "—"

    @property
    def email(self):
        return self.user.email if self.user else "—"

    @property
    def full_name(self):
        first = self.user.first_name or ''
        last = self.user.last_name or ''
        return f"{first} {last}".strip() if self.user else "—"

    @property
    def is_superuser(self):
        return self.user.is_superuser if self.user else False

    @property
    def is_staff(self):
        return self.user.is_staff if self.user else False

    @property
    def user_is_active(self):
        return self.user.is_active if self.user else False


    def save(self, *args, **kwargs):
        if not self.id:  # Generate ID only for new records
            last_owner = Owner.objects.aggregate(last_id=Max('id'))['last_id']
            
            if last_owner and "-" in last_owner:  
                try:
                    last_number = int(last_owner.split('-')[1])  # Extract numeric part
                    new_number = str(last_number + 1).zfill(3)  # Increment
                except (IndexError, ValueError):
                    new_number = "001"
            else:
                new_number = "001"

            self.id = f"OWN-{new_number}"  # Assign new ID
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} - {self.id}"


# Restaurant Model
class Restaurant(models.Model):
    TEMPLATE_CHOICES = [
        ("starter", "Starter"),
        ("modern", "Modern"),
        ("premium", "Premium"),
        ("pictorial", "Pictorial"),
    ]
    id = models.CharField(max_length=10, primary_key=True, editable=False)  # Custom formatted IDs
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name='restaurant_ownerships')
    name = models.CharField(max_length=150, default="Restaurant Name")
    address = models.TextField(default="Restaurant Address")
    phone = models.CharField(max_length=10, null=True, default="Restaurant Phone")
    email = models.EmailField(max_length=150, null=True, default="Restaurant Email")
    template = models.CharField(max_length=10, choices=TEMPLATE_CHOICES, default="starter")  # Dropdown field

    display_picture = models.ImageField(
        upload_to=restaurant_dp_upload_path,
        blank=True,
        null=True,
        default="restaurant_default_profile.jpg"
    )

    def save(self, *args, **kwargs):
        if not self.id:
            last_restaurant = Restaurant.objects.aggregate(last_id=Max('id'))['last_id']
            
            if last_restaurant and "-" in last_restaurant:  
                try:
                    last_number = int(last_restaurant.split('-')[1])  
                    new_number = str(last_number + 1).zfill(3)  
                except (IndexError, ValueError):
                    new_number = "001"
            else:
                new_number = "001"

            self.id = f"RST-{new_number}"  # Assign new ID
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.id}"


# Table Model
class Table(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='tables')
    table_number = models.IntegerField()  # Unique per restaurant
    qr_code = models.CharField(max_length=200, unique=True)  # Unique QR code for each table
    is_occupied = models.BooleanField(default=False)  

    class Meta:
        unique_together = ('restaurant', 'table_number')  # Ensures table number uniqueness within a restaurant

    def __str__(self):
        return f"Table {self.table_number} - {self.restaurant.name}"


# Menu Category Model
class MenuCategory(models.Model):
    id = models.AutoField(primary_key=True)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='category_listings')
    name = models.CharField(max_length=150, default="Category Name", null=True)
    description = models.TextField(default="Category Description")
    image_url = models.CharField(
        max_length=255,blank=True,
        help_text="Stores the URL/path of the placeholder or generated image."
    )

    def __str__(self):
        return f"{self.name} - {self.id} x {self.restaurant.name}"


# Item Tag Model
class ItemTag(models.Model):
    id = models.AutoField(primary_key=True)  
    name = models.CharField(max_length=50, blank=True, null=True, help_text="Create your own custom tags")
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.id} x {self.restaurant.name}"


# Menu Item Model
class MenuItem(models.Model):
    TYPE_CHOICES = [
        ("Veg", "Veg"),
        ("Non-Veg", "Non-Veg"),
        ("Drink", "Drink"),
    ]
    id = models.AutoField(primary_key=True)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='item_listings')
    category = models.ForeignKey(MenuCategory, on_delete=models.CASCADE, related_name='category_items')
    tags = models.ManyToManyField(ItemTag, related_name='tagged_items', blank=True)
    name = models.CharField(max_length=150)
    # price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    # is_vegetarian = models.BooleanField(default=True)

    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="Veg")
    image_url = models.CharField(
        max_length=255,blank=True,
        help_text="Stores the URL/path of the placeholder or generated image."
    )


    def __str__(self):
        return f"{self.name} - {self.id} x {self.restaurant.name} x {self.category.name} x Tags:{self.tags.name} x avail:{self.is_available}"

# Menu Item Size Model
class MenuItemSize(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='item_sizes')
    size = models.CharField(max_length=150)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_default = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        """Ensure only one default size per MenuItem"""
        if self.is_default:
            # Unset any other default sizes for the same menu item
            MenuItemSize.objects.filter(menu_item=self.menu_item, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.menu_item.name} - {self.size} - {self.price}"

# Order Model
class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),           # Just placed by customer
        ("preparing", "Preparing"),       # Accepted and being prepared
        ("ready", "Ready to Serve"),      # Food is ready to be served
        ("completed", "Completed"),       # Served and closed
        ("cancelled", "Cancelled"),       # Cancelled by staff or customer
    ]
    
    id = models.CharField(max_length=20, primary_key=True, editable=False)  # Custom formatted ID
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="restaurant_orders")
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='table_orders')
    items = models.JSONField(default=list)  
    order_no = models.PositiveSmallIntegerField()  # 3-digit order number (100-999)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = f"ord_{generate_short_uuid()}"  # Assign new ID
        # if not self.order_no:
        #     self.order_no = self.generate_unique_order_no()
        super().save(*args, **kwargs)
    
    """Generate a unique 3-digit order number for the restaurant (100-999, loops back to 101)."""
    def generate_unique_order_no(self):
        with transaction.atomic():
            today = timezone.now().date()
            used_numbers = set(
                Order.objects.filter(restaurant=self.restaurant)
                .values_list("order_no", flat=True)
            )
            for i in range(101, 1000):
                if i not in used_numbers:
                    return i
    # def generate_unique_order_no(self):
    #     with transaction.atomic():  # Prevent race conditions
    #         today_orders = Order.objects.filter(
    #             restaurant=self.restaurant, created_at__date=timezone.now().date()
    #         ).order_by("-order_no")

    #         last_order_no = today_orders.first().order_no if today_orders.exists() else 100

    #         if last_order_no >= 999:  # Reset if numbers are exhausted
    #             return 101

    #         return last_order_no + 1

    def __str__(self):
        return f"Order {self.id} - {self.restaurant.name} x {self.order_no}"
    
    class Meta:
        unique_together = ("restaurant", "order_no")


# Payment Model
class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('counter', 'Pay at Counter'),
        ('online', 'Pay Online'),
    ]
    
    id = models.CharField(max_length=20, primary_key=True, editable=False)  # Custom formatted ID
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='order_payment')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='counter')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = f"pay_{generate_short_uuid()}"  # Assign new ID
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payment for Order {self.order.id} - {self.status}"
