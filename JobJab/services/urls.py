from django.urls import path
from .views import (
    ExploreServicesView, LikeServiceView, FlagFavouriteView,
    GetServiceLikersView, DeleteServiceView, ExtendedServiceDisplayView,
    ManageServiceSectionsView, CommentServiceView, ReportContent
)
from ..booking.views import ServiceBookingView

urlpatterns = [
    path('explore/', ExploreServicesView.as_view(), name='explore_services'),
    path('<int:pk>/', ServiceBookingView.as_view(), name='service_detail'),
    path('<int:pk>/comment/', CommentServiceView.as_view(), name='comment_service'),
    path('<int:service_id>/like/', LikeServiceView.as_view(), name='like_service'),
    path('<int:service_id>/flagFavourite/', FlagFavouriteView.as_view(), name='flag_favourite'),
    path('<int:service_id>/likers/', GetServiceLikersView.as_view(), name='get_likers'),
    path('extendedServiceInfo/<int:service_id>/', ExtendedServiceDisplayView.as_view(),
         name='extended_service_display'),
    path('service/<int:service_id>/manage/', ManageServiceSectionsView.as_view(), name='manage_service_sections'),
    path('delete/<int:pk>/', DeleteServiceView.as_view(), name='delete_service'),
    path('report/', ReportContent.as_view(), name='report_content'),
]
