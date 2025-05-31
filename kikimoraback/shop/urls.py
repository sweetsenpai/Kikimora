from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from django_prometheus import exports
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .views_admin import *
from .views_admin import views_admin

urlpatterns = [
    # HOME
    path("apanel/", AdminHomePageView.as_view(), name="admin_home"),
    path("apanel/login/", AdminLogin.as_view(), name="admin_login"),
    path(
        "apanel/logout/",
        LogoutView.as_view(next_page="admin_login"),
        name="admin_logout",
    ),
    # STAFF
    path("apanel/staff/", views_admin.StaffListView.as_view(), name="staff"),
    path("apanel/staff/<int:admin_id>/", views_admin.admin_account, name="admin_account"),
    path(
        "apanel/staff/create_new_admin/",
        views_admin.AdminCreateView.as_view(),
        name="admin_create",
    ),
    # CATEGORY
    path(
        "apanel/categories/",
        views_admin.AdminCategoryView.as_view(),
        name="admin_category_view",
    ),
    path(
        "api/v1/change_visability_category/<int:category_id>/",
        views_admin.toggle_visibility_category,
        name="change_visability_category",
    ),
    # SUBCATEGORY
    path(
        "apanel/category/<int:category_id>/subcategories/",
        views_admin.AdminSubcategoryListView.as_view(),
        name="subcategory_list",
    ),
    path(
        "api/v1/change_visibility_subcat/<int:subcategory_id>/",
        views_admin.toggle_visibility_subcat,
        name="change_visibility_subcat",
    ),
    # PRODUCT
    path(
        "apanel/category/<int:category_id>/subcategories/<int:subcategory_id>/",
        views_admin.AdminProdactListView.as_view(),
        name="product_list",
    ),
    path(
        "api/v1/change_visibility_product/<int:product_id>/",
        views_admin.toggle_visibility_product,
        name="change_visibility_product",
    ),
    path(
        "apanel/product/<int:product_id>/",
        views_admin.ProductUpdateView.as_view(),
        name="product_update",
    ),
    # DISCOUNT
    path(
        "apanel/discounts/",
        views_admin.AdminDiscountListView.as_view(),
        name="discounts",
    ),
    path(
        "apanel/discounts/new_discount/",
        views_admin.AdminNewDiscount.as_view(),
        name="new_discount",
    ),
    path(
        "apanel/discounts/<int:discount_id>",
        views_admin.delete_discount,
        name="delete_discount",
    ),
    # PROMOCODS
    path(
        "apanel/promocods/",
        views_admin.AdminPromocodeListView.as_view(),
        name="promocods",
    ),
    path(
        "apanel/promocods/new_promocode/",
        views_admin.AdminNewPromo.as_view(),
        name="new_promo",
    ),
    path("apanel/promocods/<int:promo_id>/", views_admin.delete_promo, name="promocod_delete"),
    # LIMITE TIME PRODUCTS
    path(
        "apanel/day_products",
        views_admin.AdminLimitTimeProduct.as_view(),
        name="day_products",
    ),
    path(
        "apanel/day_products/<int:product_id>/",
        views_admin.AdminLimitTimeProductForm.as_view(),
        name="day_products_form",
    ),
    path("apanel/tags", views_admin.AdminTagView.as_view(), name="tags"),
    path("apanel/tags/new_tag", views_admin.AdminNewTag.as_view(), name="new-tag"),
    path(
        "apanel/tags/delete/<int:tag_id>/",
        views_admin.AdminDeleteTag.as_view(),
        name="delete_tag",
    ),
    path("apanel/metrics/", exports.ExportToDjangoView, name="prometheus-metrics"),
]
