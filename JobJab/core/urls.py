from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from JobJab.core.views import auth, location, certificates, account, payments
from django.contrib.auth import views as auth_views
from JobJab.core import main_views

urlpatterns = [
                  path('user/', include([
                      path('register/', auth.register, name='register'),
                      path('login/', auth.login, name='login'),
                      path('logout/', auth.logout, name='logout'),
                  ])),

                  path('password-reset/',
                       auth_views.PasswordResetView.as_view(template_name='core/password-auth/password-reset.html',
                                                            email_template_name='core/password-auth/password_reset_email.html',
                                                            subject_template_name='core/password-auth/password_reset_subject.txt',
                                                            success_url='/password-reset/done/'),
                       name='password_reset'),
                  path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
                      template_name='core/password-auth/password_reset_done.html'), name='password_reset_done'),
                  path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
                      template_name='core/password-auth/password_reset_confirm.html'), name='password_reset_confirm'),
                  path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
                      template_name='core/password-auth/password_reset_complete.html'), name='password_reset_complete'),

                  path('user/<str:username>/', include([
                      path('', account.account_view, name='account_view'),
                      path('connections/', account.followers_following_view, name='user_connections'),
                      path('connections/updateConnection/<int:followerId>/', account.update_followers,
                           name='update_followers'),
                      path('location-with-connections/', location.user_location_with_connections,
                           name='user_location_with_connections'),
                      path('certificates/', certificates.user_certificates, name='user_certificates'),
                      path('payments/', payments.user_payments, name='user_payments'),
                  ])),

                  path('', main_views.home, name='home'),
                  path('about/', main_views.about, name='about'),
                  path('privacyPolicy/', main_views.privacy_policy, name='privacy_policy'),
                  path('updateGeolocation/<str:username>/', location.update_geolocation, name='update_geolocation'),
                  path('certificates/delete/<int:cert_id>/', certificates.delete_certificate,
                       name='delete_certificate'),
                  path('certificates/edit/<int:certificate_id>/', certificates.edit_certificate,
                       name='edit_certificate'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
