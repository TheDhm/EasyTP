
from django.urls import path, include
from . import views

app_name = "main"

urlpatterns = [
    path('', views.homepage, name="homepage"),
    path('login/', views.login_request, name="login_request"),
    path('logout/', views.logout_request, name="logout_request"),

    path('start/<str:app_name>/', views.start_pod, name="start_pod"),
    path('start/<str:app_name>/<slug:user_id>/', views.start_pod, name="start_pod"),

    path('stop/<str:app_name>/', views.stop_pod, name="stop_pod"),
    path('stop/<str:app_name>/<slug:user_id>/', views.stop_pod, name="stop_pod"),

    path('testapps/', views.test_apps, name="test_apps"),

    path('group/', views.list_students, name="list_students"),
    path('group/<slug:group_id>/', views.list_students, name="list_students"),
    path('group/<slug:group_id>/<slug:app_id>/', views.list_students, name="list_students"),

    path('files/', views.file_explorer, name="file_explorer"),
    path('files/<path>', views.file_explorer, name="file_explorer"),
    path('download/<path>', views.download_file, name="download_file"),
]
