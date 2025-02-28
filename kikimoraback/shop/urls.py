from django.urls import path
from .views import views_admin, views_api
from django.contrib.auth.views import LoginView, LogoutView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

product_by_subcategory = views_api.ProductViewSet.as_view({'get': 'by_subcategory'})
products_with_discounts = views_api.ProductViewSet.as_view({'get': 'with_discounts'})
all_products = views_api.ProductViewSet.as_view({'get': 'all_products'})
serach_product = views_api.ProductViewSet.as_view({'get': 'search_product'})
urlpatterns = [
    # API
    # TOKEN
    path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    # REGISTRATION and LOGIN
    path('api/v1/login/', views_api.Login.as_view(), name='api-login'),
    path('api/v1/register/', views_api.RegisterUserView.as_view(), name='api-register'),
    path('api/v1/verify-email/<str:token>/', views_api.VerifyEmailView.as_view(), name='verify-email'),
    # USER DATA
    path('api/v1/user/', views_api.UserDataView.as_view(), name='api-user-data'),
    path('api/v1/user/<int:user_id>', views_api.UserDataView.as_view(), name='api-admin-user-data'),
    path('api/v1/user/order_history', views_api.UsersOrder.as_view(), name='api-order-history'),
    # PRODUCTS
    path('api/v1/categories/', views_api.CategoryList.as_view(), name='category-list'),
    path('api/v1/product/<int:product_id>/', views_api.ProductApi.as_view(), name='product'),
    path('api/v1/products/subcategory/<int:subcategory_id>/', product_by_subcategory, name='products-by-subcategory'),
    path('api/v1/products/discounts', products_with_discounts, name='products-with-discounts'),
    path('api/v1/products/all', all_products, name='all-products'),
    path('api/v1/products/search', serach_product, name='search_products'),
    path('api/v1/autocomplete/product/', views_api.ProductAutocompleteView.as_view(), name='product-autocomplete-api'),
    path('api/v1/menu/subcategory/', views_api.MenuSubcategory.as_view(), name='sub-menu'),
    path('api/v1/menu/discount_subcategory_menu/', views_api.DiscountCreationSuncategoryMenu.as_view(), name='sub-disc-menu'),
    path('api/v1/menu/discount_product_menu/<int:subcategory_id>/', views_api.DiscountCreationRelatedProducts.as_view(), name='prod-disc-menu'),
    # PRICE CHANGERS
    path('api/v1/discount', views_api.DiscountProductActiveList.as_view(), name='api-discount'),
    path('api/v1/discounts/stop/<int:discount_id>/', views_api.StopDiscountView.as_view(), name='stop_discount_api'),
    path('api//v1limitproduct', views_api.LimitProduct.as_view(), name='api-limitproduct'),
    # CRM WORK
    path('api/v1/delete_day_product/<int:limittimeproduct_id>/', views_api.DeleteDayProduct.as_view(), name='delete_day_product'),
    # DELIVERY
    path('api/v1/calculate_delivery', views_api.YandexCalculation.as_view(), name='calculate-delivery'),
    # CART
    path('api/v1/check_cart', views_api.CheckCart.as_view(), name='ckeck-cart'),
    path('api/v1/sync_cart', views_api.SyncCart.as_view(), name='sunc-cart'),
    # PROMOCODE
    path('api/v1/promo', views_api.PromoCode.as_view(), name='prom-api'),
    # PAYMENT
    path('api/v1/payment', views_api.Payment.as_view(), name='payment'),
    path('api/v1/yookassa/test', views_api.TestWebhook.as_view(), name='webhook'),
    # HOME
    path('apanel/', views_admin.AdminHomePageView.as_view(), name='admin_home'),
    path('apanel/login/', views_admin.AdminLogin.as_view(), name='admin_login'),
    path('apanel/logout/', LogoutView.as_view(next_page='admin_login'), name='admin_logout'),
    # STAFF
    path('apanel/staff/', views_admin.StaffListView.as_view(), name='staff'),
    path('apanel/staff/<int:admin_id>/', views_admin.admin_account, name='admin_account'),
    path('apanel/staff/create_new_admin/', views_admin.AdminCreateView.as_view(), name='admin_create'),
    # CATEGORY
    path('apanel/categories/', views_admin.AdminCategoryView.as_view(), name='admin_category_view'),
    path('api/v1/change_visability_category/<int:category_id>/', views_admin.toggle_visibility_category, name='change_visability_category'),
    # SUBCATEGORY
    path('apanel/category/<int:category_id>/subcategories/', views_admin.AdminSubcategoryListView.as_view(), name='subcategory_list'),
    path('api/v1/change_visibility_subcat/<int:subcategory_id>/', views_admin.toggle_visibility_subcat, name='change_visibility_subcat'),
    # PRODUCT
    path('apanel/category/<int:category_id>/subcategories/<int:subcategory_id>/', views_admin.AdminProdactListView.as_view(),
         name='prodact_list'),
    path('api/v1/change_visibility_product/<int:product_id>/', views_admin.toggle_visibility_product, name='change_visibility_product'),
    path('apanel/product/<int:product_id>/', views_admin.ProductUpdateView.as_view(), name='product_update'),
    # DISCOUNT
    path('apanel/discounts/', views_admin.AdminDiscountListView.as_view(), name='discounts'),
    path('apanel/discounts/new_discount/', views_admin.AdminNewDiscount.as_view(), name='new_discount'),
    path('apanel/discounts/<int:discount_id>', views_admin.delete_discount, name='delete_discount'),
    # PROMOCODS
    path('apanel/promocods/', views_admin.AdminPromocodeListView.as_view(), name='promocods'),
    path('apanel/promocods/new_promocode/', views_admin.AdminNewPromo.as_view(), name='new_promo'),
    path('apanel/promocods/<int:promo_id>/', views_admin.delete_promo, name='promocods'),

    # LIMITE TIME PRODUCTS
    path('apanel/day_products', views_admin.AdminLimitTimeProduct.as_view(), name='day_products'),
    path('apanel/day_products/<int:product_id>/', views_admin.AdminLimitTimeProductForm.as_view(), name='day_products_form'),

    path('apanel/tags', views_admin.AdminTagView.as_view(), name='tags')
]

