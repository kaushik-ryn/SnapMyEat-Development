from django.contrib import admin
from . import models as m

# Register your models here.

class OwnerAdmin(admin.ModelAdmin):
    list_display = ('id', 'user','username', 'email', 'phone_number', 'is_active','user_is_superuser')
    # fields = ('id',)

    def username(self, obj): return obj.username
    def email(self, obj): return obj.email
    # def full_name(self, obj): return obj.full_name
    def user_is_active(self, obj):
        return obj.user.is_active if obj.user else '❌ None'

    def user_is_superuser(self, obj):
        return obj.user.is_superuser if obj.user else '❌ None'

admin.site.register(m.Owner, OwnerAdmin)
# admin.site.register(m.Owner)
admin.site.register(m.Restaurant)
admin.site.register(m.MenuCategory)
admin.site.register(m.MenuItem)
admin.site.register(m.MenuItemSize)
admin.site.register(m.ItemTag)
admin.site.register(m.Table)
admin.site.register(m.Order)
admin.site.register(m.Payment)