from django.urls import path
from . import views


urlpatterns = [
    # API
    path('api/categories/', views.CategoryList.as_view(), name='category-list'),
    path('api/subcategories/', views.SubcategoryList.as_view(), name='subcategory-list'),
    path('api/products/', views.ProductList.as_view(), name='product-list'),
    path('api/discounts/stop/<int:discount_id>/', views.StopDiscountView.as_view(), name='stop_discount_api'),
    # HOME
    path('apanel', views.AdminHomePageView.as_view(), name='admin_home'),
    # STAFF
    path('staff', views.StaffListView.as_view(), name='staff'),
    path('staff/<int:admin_id>/', views.admin_account, name='admin_account'),
    path('staff/create_new_admin/', views.AdminCreateView.as_view(), name='admin_create'),
    # CATEGORY
    path('categories', views.AdminCategoryView.as_view(), name='admin_category_view'),
    path('change_visability/<int:category_id>/', views.toggle_visibility, name='toggle_visibility'),
    # SUBCATEGORY
    path('category/<int:category_id>/subcategories/', views.AdminSubcategoryListView.as_view(), name='subcategory_list'),
    path('change_visibility_subcat/<int:subcategory_id>/', views.toggle_visibility_subcat, name='change_visibility_subcat'),
    # PRODUCT
    path('category/<int:category_id>/subcategories/<int:subcategory_id>', views.AdminProdactListView.as_view(),
         name='prodact_list'),
    path('change_visibility_product/<int:product_id>/', views.toggle_visibility_product, name='change_visibility_product'),
    path('product/<int:product_id>', views.ProductUpdateView.as_view(), name='product_update'),
    # DISCOUNT
    path('discounts', views.AdminDiscountListView.as_view(), name='discounts'),
    path('discounts/new_discount', views.AdminNewDiscount.as_view(), name='new_discount'),
    path('discounts/<int:discount_id>', views.delete_discount, name='delete_discount')
]

