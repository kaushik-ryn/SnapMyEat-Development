from django.urls import path
from staff import views


urlpatterns = [

    path("",views.home,name="management-home"),
    path("orders",views.orders,name="management-orders"),
    path("see/all/orders",views.see_orders,name="management-seeOrders"),
    path("update-order-status/", views.update_order_status, name="update-order-status"),

    path("menu/items",views.menu_items,name="management-menu"),
    path("menu/items/add",views.menu_items_add,name="management-menu-add"),
    path("menu/items/del/<int:itemID>",views.menu_items_del,name="management-menu-del"),
    path("menu/items/edit/<int:itemID>",views.menu_items_edit,name="management-menu-edit"),

    path("menu/categories",views.menu_category,name="management-category"),
    path("menu/categories/add",views.menu_category_add,name="management-category-add"),
    path("menu/categories/del/<int:categoryID>",views.menu_category_del,name="management-category-del"),
    path("menu/categories/edit/<int:categoryID>",views.menu_category_edit,name="management-category-edit"),
    
    path("menu/tags",views.menu_tags,name="management-tags"),
    path("menu/tag/del/<int:tagID>",views.menu_tags_del,name="management-tag-del"),
    path("menu/tag/edit/<int:tagID>",views.menu_tags_edit,name="management-tag-edit"),
    
    path("table/qr",views.table_qr,name="management-table"),
    # generate qr
    path("qr/<int:table_number>/generate/barcode", views.generate_table_qr, name="generate_table_qr"),

    path("insights",views.insight,name="management-insights"),

    path("profile/restaurant/",views.profile,name="management-profile"),

    path("logout/",views.management_logout,name="management-logout"),
    path("upgrade/", views.upgrade, name="management-upgrade"),

    # AJAX API
    path("fetch-image/", views.get_image_by_name, name="ajax-fetch-image"),
    path("generate-description/", views.generate_category_description, name="description-generate"),
    

]
