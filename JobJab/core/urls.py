from django.urls import path, include  # Make sure 'include' is imported
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('user/', include([
        path('register/', views.register, name='register'),
        path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
        path('logout/', auth_views.LogoutView.as_view(template_name='core/logout.html'), name='logout'),
    ])),
    path('', views.home, name='home'),
]