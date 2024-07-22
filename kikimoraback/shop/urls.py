from django.urls import path
from . import views


urlpatterns = [
    path('apanel', views.AdminHomePageView.as_view(), name='admin_home'),
    path('staff', views.apanel_staff),
    path('staff/<int:admin_id>/', views.admin_account, name='admin_account')
            ]