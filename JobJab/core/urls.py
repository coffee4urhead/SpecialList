from django.urls import path, include  # Make sure 'include' is imported
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('user/', include([
        path('register/', views.register, name='register'),
        path('login/', views.login, name='login'),
        path('logout/', views.logout, name='logout'),
    ])),
    path('', views.home, name='home'),
]