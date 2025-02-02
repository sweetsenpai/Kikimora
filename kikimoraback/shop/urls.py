from django.urls import path
from .views import views_admin, views_api
from django.contrib.auth.views import LoginView, LogoutView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

product_by_subcategory = views_api.ProductViewSet.as_view({'get': 'by_subcategory'})
product_by_category = views_api.ProductViewSet.as_view({'get': 'by_category'})

urlpatterns = [
    # API
    # TOKEN
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    # REGISTRATION and LOGIN
    path('api/login/', views_api.Login.as_view(), name='api-login'),
    path('api/register/', views_api.RegisterUserView.as_view(), name='api-register'),
    # USER DATA
    path('api/user/', views_api.UserDataView.as_view(), name='api-user-data'),
    path('api/user/<int:user_id>', views_api.UserDataView.as_view(), name='api-admin-user-data'),
    path('api/user/order_history', views_api.UsersOrder.as_view(), name='api-order-history'),
    # PRODUCTS
    path('api/categories/', views_api.CategoryList.as_view(), name='category-list'),
    path('api/product/<int:product_id>/', views_api.ProductApi.as_view(), name='product'),
    path('api/products/subcategory/<int:subcategory_id>/', product_by_subcategory, name='products-by-subcategory'),
    path('api/products/category/<int:category_id>/', product_by_category, name='products-by-category'),
    path('api/autocomplete/product/', views_api.ProductAutocompleteView.as_view(), name='product-autocomplete-api'),
    path('api/menu/subcategory/', views_api.MenuSubcategory.as_view(), name='sub-menu'),
    # PRICE CHANGERS
    path('api/discount', views_api.DiscountProductActiveList.as_view(), name='api-discount'),
    path('api/discounts/stop/<int:discount_id>/', views_api.StopDiscountView.as_view(), name='stop_discount_api'),
    path('api/limitproduct', views_api.LimitProduct.as_view(), name='api-limitproduct'),
    # CRM WORK
    path('api/delete_day_product/<int:limittimeproduct_id>/', views_api.DeleteDayProduct.as_view(), name='delete_day_product'),
    # DELIVERY
    path('api/calculate_delivery', views_api.YandexCalculation.as_view(), name='calculate-delivery'),
    # CART
    path('api/check_cart', views_api.CheckCart.as_view(), name='ckeck-cart'),
    path('api/sync_cart', views_api.SyncCart.as_view(), name='sunc-cart'),
    # PROMOCODE
    path('api/promo', views_api.PromoCode.as_view(), name='prom-api'),
    # PAYMENT
    path('api/payment', views_api.Payment.as_view(), name='payment'),
    path('api/yookassa/test', views_api.TestWebhook.as_view(), name='webhook'),
    # HOME
    path('apanel', views_admin.AdminHomePageView.as_view(), name='admin_home'),
    path('apanel/login', views_admin.AdminLogin.as_view(), name='admin_login'),
    path('apanel/logout', LogoutView.as_view(next_page='admin_login'), name='admin_logout'),
    # STAFF
    path('staff', views_admin.StaffListView.as_view(), name='staff'),
    path('staff/<int:admin_id>/', views_admin.admin_account, name='admin_account'),
    path('staff/create_new_admin/', views_admin.AdminCreateView.as_view(), name='admin_create'),
    # CATEGORY
    path('categories', views_admin.AdminCategoryView.as_view(), name='admin_category_view'),
    path('change_visability_category/<int:category_id>/', views_admin.toggle_visibility_category, name='change_visability_category'),
    # SUBCATEGORY
    path('category/<int:category_id>/subcategories/', views_admin.AdminSubcategoryListView.as_view(), name='subcategory_list'),
    path('change_visibility_subcat/<int:subcategory_id>/', views_admin.toggle_visibility_subcat, name='change_visibility_subcat'),
    # PRODUCT
    path('category/<int:category_id>/subcategories/<int:subcategory_id>', views_admin.AdminProdactListView.as_view(),
         name='prodact_list'),
    path('change_visibility_product/<int:product_id>/', views_admin.toggle_visibility_product, name='change_visibility_product'),
    path('product/<int:product_id>', views_admin.ProductUpdateView.as_view(), name='product_update'),
    # DISCOUNT
    path('discounts', views_admin.AdminDiscountListView.as_view(), name='discounts'),
    path('discounts/new_discount', views_admin.AdminNewDiscount.as_view(), name='new_discount'),
    path('discounts/<int:discount_id>', views_admin.delete_discount, name='delete_discount'),
    # PROMOCODS
    path('promocods', views_admin.AdminPromocodeListView.as_view(), name='promocods'),
    path('promocods/new_promocode', views_admin.AdminNewPromo.as_view(), name='new_promo'),
    path('promocods/<int:promo_id>', views_admin.delete_promo, name='promocods'),

    # LIMITE TIME PRODUCTS
    path('day_products', views_admin.AdminLimitTimeProduct.as_view(), name='day_products'),
    path('day_products/<int:product_id>/', views_admin.AdminLimitTimeProductForm.as_view(), name='day_products_form')
]

