from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser,UserAddress, OrdersHistory, Category, Product, Discount
from .forms import CustomUserCreationForm, CustomUserChangeForm


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ["email", "bd", "user_fio", "phone"]


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(UserAddress)
admin.site.register(OrdersHistory)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Discount)