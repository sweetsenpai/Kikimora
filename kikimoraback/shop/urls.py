from django.urls import path
from . import views


urlpatterns = [
    path('apanel', views.AdminHomePageView.as_view(), name='admin_home'),
    path('staff', views.StaffListView.as_view(), name='staff'),
    path('staff/<int:admin_id>/', views.admin_account, name='admin_account'),
    path('staff/create_new_admin/', views.AdminCreateView.as_view(), name='admin_create'),
    path('categories', views.AdminCategoryView.as_view(), name='admin_category_view'),
    path('change_visability/<int:category_id>/', views.toggle_visibility, name='toggle_visibility'),
    path('change_visability/<int:category_id>/', views.toggle_visibility, name='toggle_visibility'),
    path('category/<int:category_id>/subcategories/', views.AdminSubcategoryListView.as_view(), name='subcategory_list'),
]