

from django.urls import path

from customer import views as customer_views

urlpatterns = [
    path('menu-items/', customer_views.menu_items, name='menu_items'),
    path('menu-categories/', customer_views.menu_category, name='menu_categories'),
    path('order-summary/', customer_views.order_summary, name='order_summary'),
    path('placed-order/', customer_views.placed_order, name='placed_order'),
    path('order-details/', customer_views.order_details, name='order_details'),
    path('order-history/', customer_views.view_order, name='view_order'),
    


]
