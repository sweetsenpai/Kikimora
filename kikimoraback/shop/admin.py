from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, UserAddress, OrdersHistory, Category, Product, Discount, UserBonusSystem
from .forms import UserCreationForm, UserChangeForm


class AccountAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ('email', 'user_fio', 'phone', 'bd', 'date_joined', 'is_staff',  'is_superuser')
    list_filter = ('is_superuser',)

    fieldsets = (
        (None, {'fields': ('email', 'is_staff', 'is_superuser', 'password')}),
        ('Personal info', {'fields': ('user_fio', 'phone', 'bd', 'date_joined')}),
        ('Groups', {'fields': ('groups',)}),
        ('Permissions', {'fields': ('user_permissions',)}),
    )
    add_fieldsets = (
        (None, {'fields': ('email', 'is_staff', 'is_superuser', 'password1', 'password2')}),
        ('Personal info', {'fields': ('user_fio', 'phone', 'bd', 'date_joined')}),
        ('Groups', {'fields': ('groups',)}),
        ('Permissions', {'fields': ('user_permissions',)}),
    )

    search_fields = ('email', 'user_fio', 'phone')
    ordering = ('email',)
    filter_horizontal = ()


admin.site.register(CustomUser, AccountAdmin)
admin.site.register(UserBonusSystem)
admin.site.register(UserAddress)
admin.site.register(OrdersHistory)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Discount)