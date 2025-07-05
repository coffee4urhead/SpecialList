from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from JobJab.core.views import auth, location, certificates, account
from JobJab.core import main_views

urlpatterns = [
                  path('user/', include([
                      path('register/', auth.register, name='register'),
                      path('login/', auth.login, name='login'),
                      path('logout/', auth.logout, name='logout'),
                  ])),

                  path('user/<str:username>/', include([
                      path('', account.account_view, name='account_view'),
                      path('connections/', account.followers_following_view, name='user_connections'),
                      path('connections/updateConnection/<int:followerId>/', account.update_followers, name='update_followers'),
                      path('location-with-connections/', location.user_location_with_connections,
                           name='user_location_with_connections'),
                      path('certificates/', certificates.user_certificates, name='user_certificates'),
                  ])),

                  path('', main_views.home, name='home'),
                  path('about/', main_views.about, name='about'),
                  path('privacyPolicy/', main_views.privacy_policy, name='privacy_policy'),
                  path('updateGeolocation/<str:username>/', location.update_geolocation, name='update_geolocation'),
                  path('certificates/delete/<int:pk>/', certificates.delete_certificate, name='delete_certificate'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
