from django.urls import path
from . import views
urlpatterns = [
path('apanel', views.apanel_home)
]