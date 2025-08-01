from datetime import timedelta

import pandas as pd
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views import View
from plotly import graph_objects as go
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.db.models import Count

from JobJab.booking.models import Booking
from JobJab.chats.models import Conversation, Message
from JobJab.core.models import Organization, CustomUser, Certificate, BlacklistItem, UserBlacklistProfile, \
    BlacklistStatus, Notification, NotificationType
import plotly.express as px
from plotly.offline import plot

from JobJab.reviews.models import WebsiteReview, UserReview
from JobJab.services.models import Availability, Comment, ServiceListing
from JobJab.subscriptions.models import SubscriptionRecord


class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'admin_home.html'
    login_url = 'login'
    paginate_by = 5

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(self.get_login_url())

        messages.error(self.request, "Staff privileges required")
        return redirect(self.get_login_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        disputes = BlacklistItem.objects.all().select_related(
            'reporter', 'moderator', 'content_type'
        )

        paginator = Paginator(disputes, self.paginate_by)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        banned_profiles = UserBlacklistProfile.objects.filter(is_banned=True).select_related('user')
        warned_profiles = UserBlacklistProfile.objects.filter(warning_count__gt=0, is_banned=False).select_related(
            'user')

        user_ct = ContentType.objects.get_for_model(CustomUser)
        service_ct = ContentType.objects.get_for_model(ServiceListing)
        review_ct = ContentType.objects.get_for_model(UserReview)
        comment_ct = ContentType.objects.get_for_model(Comment)

        context.update({
            'disputes': disputes,
            'banned_profiles': banned_profiles,
            'warned_profiles': warned_profiles,
            'page_obj': page_obj,
            'reported_users_count': BlacklistItem.objects.filter(
                content_type=user_ct,
                status=BlacklistStatus.PENDING
            ).count(),
            'reported_services_count': BlacklistItem.objects.filter(
                content_type=service_ct,
                status=BlacklistStatus.PENDING
            ).count(),
            'reported_reviews_count': BlacklistItem.objects.filter(
                content_type=review_ct,
                status=BlacklistStatus.PENDING
            ).count(),
            'reported_comments_count': BlacklistItem.objects.filter(
                content_type=comment_ct,
                status=BlacklistStatus.PENDING
            ).count(),
            'user_ct': user_ct,
            'service_ct': service_ct,
            'review_ct': review_ct,
            'comment_ct': comment_ct,
        })

        return context


class GraphsView:
    """Handles all graph generation logic"""

    @staticmethod
    def create_user_registration_graph(data, time_period):

        df = pd.DataFrame(list(data))

        if df.empty or 'date' not in df.columns or 'count' not in df.columns:
            today = timezone.now().date()
            df = pd.DataFrame([{'date': today, 'count': 0}])

        df['date'] = pd.to_datetime(df['date'])

        df['count'] = df['count'].astype(int)

        date_range = pd.date_range(start=df['date'].min(), end=df['date'].max(), freq='D')
        df = df.set_index('date').reindex(date_range, fill_value=0).reset_index()
        df.rename(columns={'index': 'date'}, inplace=True)

        fig = px.line(
            df,
            x='date',
            y='count',
            title=f'User Registrations ({time_period})',
            labels={'date': 'Date', 'count': 'New Users'},
            color_discrete_sequence=['#06BAC5'],
            template='plotly_white'
        )

        fig.update_traces(mode='lines+markers', marker=dict(size=6))
        fig.update_layout(
            hovermode='x unified',
            xaxis_title='Date',
            yaxis_title='New Registrations',
            margin=dict(l=40, r=40, t=80, b=40),
            showlegend=False,
        )

        if len(df) > 1:
            frames = [
                go.Frame(
                    data=[go.Scatter(
                        x=df['date'].iloc[:i],
                        y=df['count'].iloc[:i],
                        mode='lines+markers'
                    )],
                    name=f'frame_{i}'
                )
                for i in range(1, len(df) + 1)
            ]
            fig.frames = frames
            fig.update_layout(
                updatemenus=[dict(
                    type="buttons",
                    showactive=False,
                    buttons=[dict(label="Play", method="animate", args=[None])],
                )]
            )

        return plot(fig, output_type='div', include_plotlyjs='cdn')

    @staticmethod
    def create_certificate_status_graph(certificates):
        """Creates certificate status bar chart"""
        status_counts = certificates.values('is_verified').annotate(count=Count('id'))

        df = pd.DataFrame(list(status_counts))

        if len(df['is_verified'].unique()) < 2:
            all_statuses = pd.DataFrame({
                'is_verified': [True, False],
                'count': [0, 0]
            })
            df = pd.concat([df, all_statuses]).groupby('is_verified').max().reset_index()

        fig = px.bar(
            df,
            x='is_verified',
            y='count',
            color='is_verified',
            title='Certificate Verification Status',
            labels={'is_verified': 'Status', 'count': 'Count'},
            color_discrete_map={True: '#32AE88', False: '#008DAA'},
            width=400,
            height=600
        )

        fig.update_layout(
            hovermode='x unified',
            xaxis=dict(
                tickmode='array',
                tickvals=[False, True],
                ticktext=['Unverified', 'Verified'],
                title='Verification Status'
            ),
            yaxis=dict(title='Number of Certificates'),
            plot_bgcolor='white',
            paper_bgcolor='white',
            hoverlabel=dict(
                bgcolor="white",
                font_size=16,
                font_family="Rockwell"
            )
        )

        config = {
            'displayModeBar': True,
            'modeBarButtonsToAdd': ['hoverclosest', 'hovercompare'],
            'responsive': True
        }

        return plot(fig, output_type='div', config=config, include_plotlyjs='cdn')

    @staticmethod
    def create_service_trend_graph(services, start_date, end_date, arg_getter='created_at'):
        df = pd.DataFrame(
            services.annotate(date=TruncDate(arg_getter))
            .values('date')
            .annotate(count=Count('id'))
        )

        if df.empty:
            df = pd.DataFrame([{'date': start_date.date(), 'count': 0}])

        df['date'] = pd.to_datetime(df['date'])
        date_range = pd.date_range(start=start_date, end=end_date)
        df = df.set_index('date').reindex(date_range, fill_value=0).reset_index()
        df.rename(columns={'index': 'date'}, inplace=True)

        fig = px.bar(
            df, x='date', y='count', title='New Services Over Time',
            labels={'date': 'Date', 'count': 'New Services'},
            color_discrete_sequence=['#4D9DE0']
        )
        return plot(fig, output_type='div', include_plotlyjs='cdn')

    @staticmethod
    def create_availability_status_graph(availabilities):
        df = pd.DataFrame(
            availabilities.values('status').annotate(count=Count('id'))
        )

        if df.empty:
            df = pd.DataFrame({'status': [], 'count': []})

        fig = px.bar(
            df,
            x='status',
            y='count',
            title='Availability Status Distribution',
            labels={'status': 'Status', 'count': 'Count'},
            color_discrete_sequence=['#6c757d']
        )

        fig.update_layout(
            hovermode='x unified',
            xaxis_title='Status',
            yaxis_title='Number of Entries',
            plot_bgcolor='white',
            paper_bgcolor='white',
            showlegend=False
        )

        return plot(fig, output_type='div', include_plotlyjs='cdn')

    @staticmethod
    def create_comment_activity_graph(comments, start_date, end_date):
        df = pd.DataFrame(
            comments.annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(count=Count('id'))
        )

        if df.empty:
            df = pd.DataFrame([{'date': start_date.date(), 'count': 0}])

        df['date'] = pd.to_datetime(df['date'])
        date_range = pd.date_range(start=start_date, end=end_date)
        df = df.set_index('date').reindex(date_range, fill_value=0).reset_index()
        df.rename(columns={'index': 'date'}, inplace=True)

        print(df)
        fig = px.line(
            df, x='date', y='count', title='Comment Activity',
            labels={'date': 'Date', 'count': 'Comments'},
            color_discrete_sequence=['#FF715B']
        )
        return plot(fig, output_type='div', include_plotlyjs='cdn')


class CoreInfoView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'template-admin-components/admin_core_info.html'
    login_url = 'login'

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        time_period = f"{start_date.strftime('%b %d')} to {end_date.strftime('%b %d')}"

        registration_data = (
            CustomUser.objects
            .filter(date_joined__range=(start_date, end_date))
            .annotate(date=TruncDate('date_joined'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )

        if not registration_data:
            registration_data = [{'date': start_date.date(), 'count': 0}]

        certificates = Certificate.objects.all()
        cert_graph_html = GraphsView.create_certificate_status_graph(certificates)

        context.update({
            'organizations': Organization.objects.annotate(member_count=Count('members')).order_by('-member_count'),
            'total_users': CustomUser.objects.count(),
            'users': CustomUser.objects.all(),
            'total_organizations': Organization.objects.count(),
            'unverified_certs_count': Certificate.objects.filter(is_verified=False).count(),
            'unverified_certs': Certificate.objects.filter(is_verified=False),
            'time_period': time_period,
            'user_registration_graph': GraphsView.create_user_registration_graph(
                registration_data,
                time_period
            ),
            'certificate_graph': cert_graph_html,
        })
        return context

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(self.get_login_url())
        messages.error(self.request, "Staff privileges required")
        return redirect(self.get_login_url())


class ServicesInfoView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'template-admin-components/admin_services_info.html'
    login_url = 'login'

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(self.get_login_url())
        messages.error(self.request, "Staff privileges required")
        return redirect(self.get_login_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)

        services = ServiceListing.objects.select_related('provider').all()
        recent_services = services.filter(created_at__range=(start_date, end_date))
        availabilities = Availability.objects.all()
        comments = Comment.objects.select_related('author').all()

        context.update({
            'total_services': services.count(),
            'recent_services': recent_services,
            'availabilities': availabilities,
            'comments': comments,
            'services': services,

            'service_graph': GraphsView.create_service_trend_graph(services, start_date, end_date),
            'availability_graph': GraphsView.create_availability_status_graph(availabilities),
            'comment_graph': GraphsView.create_comment_activity_graph(comments, start_date, end_date),
        })
        return context


class SubscriptionsInfoView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'template-admin-components/admin_subscriptions_info.html'
    login_url = 'login'

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(self.get_login_url())
        messages.error(self.request, "Staff privileges required")
        return redirect(self.get_login_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)

        subscriptions = SubscriptionRecord.objects.select_related('user').all()
        recent_subscriptions = subscriptions.filter(created_at__range=(start_date, end_date))

        context.update({
            'total_subscriptions': subscriptions.count(),
            'recent_subscriptions': recent_subscriptions,
            'subscriptions': subscriptions,

            'subscriptions_graph': GraphsView.create_service_trend_graph(subscriptions, start_date, end_date),
        })
        return context


class ChatsInfoView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'template-admin-components/admin_chats_info.html'
    login_url = 'login'

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(self.get_login_url())
        messages.error(self.request, "Staff privileges required")
        return redirect(self.get_login_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)

        chats = Conversation.objects.prefetch_related('participants').all()
        recent_chats = chats.filter(created_at__range=(start_date, end_date))
        messages = Message.objects.select_related('sender').all()
        messages_count = messages.count()

        context.update({
            'total_chats': chats.count(),
            'total_messages': messages_count,
            'messages': messages,
            'recent_chats': recent_chats,
            'chats': chats,

            'messages_graph': GraphsView.create_service_trend_graph(messages, start_date, end_date,
                                                                    arg_getter='timestamp'),
            'chats_graph': GraphsView.create_service_trend_graph(chats, start_date, end_date),
        })
        return context


class ReviewsInfoView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'template-admin-components/admin_reviews_info.html'
    login_url = 'login'

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(self.get_login_url())
        messages.error(self.request, "Staff privileges required")
        return redirect(self.get_login_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)

        website_reviews = WebsiteReview.objects.prefetch_related('reviewer').all()

        user_reviews = UserReview.objects.select_related('reviewer', 'reviewee').all()

        context.update({
            'total_web_reviews': website_reviews.count(),
            'total_user_reviews': user_reviews.count(),
            'website_reviews': website_reviews,
            'user_reviews': user_reviews,

            'website_reviews_graph': GraphsView.create_service_trend_graph(website_reviews, start_date, end_date),
            'user_reviews_graph': GraphsView.create_service_trend_graph(user_reviews, start_date, end_date),
        })
        return context


class BookingInfoView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'template-admin-components/admin_booking_info.html'
    login_url = 'login'

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(self.get_login_url())
        messages.error(self.request, "Staff privileges required")
        return redirect(self.get_login_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)

        bookings = Booking.objects.prefetch_related('seeker', 'provider').all()

        context.update({
            'total_bookings': bookings.count(),
            'bookings': bookings,

            'bookings_graph': GraphsView.create_service_trend_graph(bookings, start_date, end_date),
        })
        return context


class ResolveDisputes(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff

    def post(self, request, dispute_id=None, action=None, reviewee=None):
        try:
            dispute_id = dispute_id or request.POST.get('dispute_id') or request.data.get('dispute_id')
            action = action or request.POST.get('action') or request.data.get('action')

            if not dispute_id or not action:
                return JsonResponse({'status': 'error', 'message': 'Missing parameters'}, status=400)

            dispute = BlacklistItem.objects.get(id=dispute_id)

            if action == 'approve':
                dispute.approve_report(moderator=request.user)
                Notification.create_notification(
                    user=dispute.reporter,
                    title=f"Successfully approved you report!",
                    message="Thank you for your report. Make sure the community remains safe and threat free!",
                    notification_type=NotificationType.BAN
                )

                if hasattr(dispute.content_object, 'user') and dispute.content_object.user != dispute.reporter:
                    Notification.objects.create(
                        user=dispute.content_object.user,
                        title="Content Violation",
                        message=f"Your {dispute.content_type.model} was removed for violating our policies",
                        notification_type=NotificationType.WARNING
                    )

            elif action == 'reject':
                dispute.reject_report(moderator=request.user)
                Notification.create_notification(
                    user=dispute.reporter,
                    title=f"Your report has been rejected!",
                    message="Keep in mind that any future false reports may result in bans to your account. Be mindful what yiu report and for what reason - everything is reviews by our admins!",
                    notification_type=NotificationType.WARNING
                )
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid action'}, status=400)

            return JsonResponse({'status': 'success'})

        except BlacklistItem.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Dispute not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
