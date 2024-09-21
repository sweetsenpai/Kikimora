from django.urls import path
from .views import views_admin, views_api


urlpatterns = [
    # API
    path('api/categories/', views_api.CategoryList.as_view(), name='category-list'),
    path('api/subcategories/', views_api.SubcategoryList.as_view(), name='subcategory-list'),
    path('api/products/', views_api.ProductList.as_view(), name='product-list'),
    path('api/autocomplete/product/', views_api.ProductAutocompleteView.as_view(), name='product-autocomplete-api'),
    path('api/discounts/stop/<int:discount_id>/', views_api.StopDiscountView.as_view(), name='stop_discount_api'),
    path('api/delete_day_product/<int:limittimeproduct_id>/', views_api.DeleteDayProduct.as_view(), name='delete_day_product'),
    # HOME
    path('apanel', views_admin.AdminHomePageView.as_view(), name='admin_home'),
    # STAFF
    path('staff', views_admin.StaffListView.as_view(), name='staff'),
    path('staff/<int:admin_id>/', views_admin.admin_account, name='admin_account'),
    path('staff/create_new_admin/', views_admin.AdminCreateView.as_view(), name='admin_create'),
    # CATEGORY
    path('categories', views_admin.AdminCategoryView.as_view(), name='admin_category_view'),
    path('change_visability/<int:category_id>/', views_admin.toggle_visibility, name='toggle_visibility'),
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

