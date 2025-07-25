from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from JobJab.core import main_views
from JobJab.core.views import (
    auth, location, certificates, account, payments
)

urlpatterns = [
    path('user/', include([
        path('register/', auth.RegisterView.as_view(), name='register'),
        path('login/', auth.LoginView.as_view(), name='login'),
        path('logout/', auth.LogoutView.as_view(), name='logout'),
    ])),

    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='core/password-auth/password-reset.html',
             email_template_name='core/password-auth/password_reset_email.html',
             subject_template_name='core/password-auth/password_reset_subject.txt',
             success_url='/password-reset/done/'),
         name='password_reset'),

    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='core/password-auth/password_reset_done.html'),
         name='password_reset_done'),

    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='core/password-auth/password_reset_confirm.html'),
         name='password_reset_confirm'),

    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='core/password-auth/password_reset_complete.html'),
         name='password_reset_complete'),

    path('user/<str:username>/', include([
        path('', account.AccountView.as_view(), name='account_view'),
        path('connections/', account.FollowersFollowingView.as_view(), name='user_connections'),
        path('connections/updateConnection/<int:followerId>/',
             account.UpdateFollowersView.as_view(), name='update_followers'),
        path('location-with-connections/',
             location.UserLocationWithConnectionsView.as_view(), name='user_location_with_connections'),
        path('certificates/', certificates.UserCertificatesView.as_view(), name='user_certificates'),
        path('payments/', payments.UserPaymentsView.as_view(), name='user_payments'),
    ])),

    path('', main_views.HomeView.as_view(), name='home'),
    path('about/', main_views.AboutView.as_view(), name='about'),
    path('privacyPolicy/', main_views.PrivacyPolicyView.as_view(), name='privacy_policy'),

    path('updateGeolocation/<str:username>/',
         location.UpdateGeolocationView.as_view(), name='update_geolocation'),
    path('certificates/delete/<int:cert_id>/',
         certificates.DeleteCertificateView.as_view(), name='delete_certificate'),
    path('certificates/edit/<int:certificate_id>/',
         certificates.EditCertificateView.as_view(), name='edit_certificate'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
