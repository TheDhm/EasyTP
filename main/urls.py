
from django.urls import path, include
from . import views

app_name = "main"

urlpatterns = [
    path('', views.homepage, name="homepage"),
    path('login/', views.login_request, name="login_request"),
    path('logout/', views.logout_request, name="logout_request"),
    path('refresh_instances/', views.watch_dog_notification, name="watch_dog_notification"),
    path('start/<str:app>/', views.start_container, name="start_container"),
    path('stop/<str:app>/', views.stop_container, name="stop_container"),
]
