from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .api_views import *

product_by_subcategory = ProductViewSet.as_view({"get": "by_subcategory"})
products_with_discounts = ProductViewSet.as_view({"get": "with_discounts"})
all_products = ProductViewSet.as_view({"get": "all_products"})
serach_product = ProductViewSet.as_view({"get": "search_product"})

urlpatterns = [
    # API
    # TOKEN
    path("api/v1/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/v1/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/v1/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # REGISTRATION and LOGIN
    path("api/v1/login/", Login.as_view(), name="api-login"),
    path("api/v1/register/", RegisterUserView.as_view(), name="api-register"),
    path(
        "api/v1/verify-email/<str:token>/",
        VerifyEmailView.as_view(),
        name="verify-email",
    ),
    # USER DATA
    path("api/v1/user/", UserDataView.as_view(), name="api-user-data"),
    path(
        "api/v1/user/<int:user_id>", UserDataView.as_view(), name="api-admin-user-data"
    ),
    path("api/v1/user/order_history", UsersOrder.as_view(), name="api-order-history"),
    # PRODUCTS
    path("api/v1/categories/", CategoryList.as_view(), name="category-list"),
    path("api/v1/product/<slug:product_slug>/", ProductApi.as_view(), name="product"),
    path(
        "api/v1/products/subcategory/<slug:subcategory_slug>/",
        product_by_subcategory,
        name="products-by-subcategory",
    ),
    path(
        "api/v1/products/discounts",
        products_with_discounts,
        name="products-with-discounts",
    ),
    path("api/v1/products/all", all_products, name="all-products"),
    path("api/v1/products/search", serach_product, name="search_products"),
    path("api/v1/menu/subcategory/", MenuSubcategory.as_view(), name="sub-menu"),
    path(
        "api/v1/menu/discount_product_menu/<int:subcategory_id>/",
        DiscountCreationRelatedProducts.as_view(),
        name="prod-disc-menu",
    ),
    # PRICE CHANGERS
    path("api/v1/discount", DiscountProductActiveList.as_view(), name="api-discount"),
    path(
        "api/v1/discounts/stop/<int:discount_id>/",
        StopDiscountView.as_view(),
        name="stop_discount_api",
    ),
    path("api/v1/limitproduct", LimitProduct.as_view(), name="api-limitproduct"),
    # CRM WORK
    path(
        "api/v1/delete_day_product/<int:limittimeproduct_id>/",
        DeleteDayProduct.as_view(),
        name="delete_day_product",
    ),
    # CART
    path("api/v1/sync_cart", SyncCart.as_view(), name="sunc-cart"),
    # PROMOCODE
    path("api/v1/promo", PromoCode.as_view(), name="prom-api"),
    # PAYMENT
    path("api/v1/orderpath", OrderPath.as_view(), name="order-path"),
    path("api/v1/yookassa/test", TestWebhook.as_view(), name="webhook"),
    path("api/v1/feedback", FeedBackApi.as_view(), name="feedback"),
]
