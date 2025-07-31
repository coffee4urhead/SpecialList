from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import DeleteView
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q, Prefetch

from JobJab.services.models import ServiceListing, Comment
from .forms import ServiceListingForm, ServiceDetailSectionFormSet, CommentForm
from .utils import get_service_limit_for_plan
from .. import settings
from ..booking.forms import ProviderAvailabilityForm
from ..booking.models import ProviderAvailability, WeeklyTimeSlot
from ..core.forms import BlacklistItemForm
from ..core.models import CustomUser, BlacklistReason, BlacklistStatus, BlacklistItem, Notification, NotificationType
from ..reviews.models import UserReview
from ..subscriptions.models import SubscriptionPlan, SubscriptionStatus

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']


class ExploreServicesView(LoginRequiredMixin, View):
    login_url = 'login'
    template_name = 'explore_services.html'

    def get(self, request):
        user = request.user
        services = ServiceListing.objects.filter(is_active=True)

        show_verified = request.GET.get('verified') == 'true'
        show_freelancers = request.GET.get('freelancers') == 'true'
        price_range = request.GET.get('price_range')
        location_filter = request.GET.get('location')

        if location_filter:
            parts = location_filter.split('/')
            if len(parts) == 2:
                country, region = parts
                services = services.filter(Q(location__icontains=country) & Q(location__icontains=region))
            else:
                services = services.filter(location__icontains=location_filter)

        if show_verified:
            services = services.filter(provider__is_verified=True)

        if show_freelancers:
            services = services.filter(
                Q(provider__user_type='Freelancer') &
                Q(provider__subscription_membership__plan=SubscriptionPlan.STARTER) &
                Q(provider__subscription_membership__status=SubscriptionStatus.ACTIVE) &
                Q(provider__subscription_membership__current_period_start__lte=timezone.now()) &
                Q(provider__subscription_membership__current_period_end__gte=timezone.now())
            )

        if price_range:
            min_price, max_price = map(float, price_range.split('-'))
            services = services.filter(price__gte=min_price, price__lte=max_price)

        subscription = user.subscription_membership
        plan = subscription.plan if subscription else 'No plan'
        allowed_services = get_service_limit_for_plan(plan)
        service_count = services.count()
        can_create_more = service_count < allowed_services
        context = {
            'form': ServiceListingForm(),
            'services': services,
            'user_services': services.filter(provider=user),
            'plan': plan,
            'allowed_services': allowed_services,
            'service_count': service_count,
            'can_create_more': can_create_more,
            'current_filters': {
                'verified': show_verified,
                'freelancers': show_freelancers,
                'price_range': price_range,
                'location': location_filter,
            },
        }
        return render(request, self.template_name, context)

    def post(self, request):
        user = request.user
        subscription = user.subscription_membership
        plan = subscription.plan if subscription else 'No plan'
        allowed_services = get_service_limit_for_plan(plan)
        service_count = ServiceListing.objects.filter(provider=user).count()

        if service_count >= allowed_services:
            return redirect('explore_services')

        form = ServiceListingForm(request.POST, request.FILES)
        if form.is_valid():
            service = form.save(commit=False)
            service.provider = user
            service.save()

            Notification.create_notification(
                user=request.user,
                title=f"Successfully created a service",
                message="Welcome to our community! You can now start your business journey!",
                notification_type=NotificationType.INFO
            )
        return redirect('explore_services')


class LikeServiceView(LoginRequiredMixin, View):
    def post(self, request, service_id):
        service = get_object_or_404(ServiceListing, id=service_id)
        user = request.user
        if user in service.likes.all():
            service.likes.remove(user)
            liked = False
        else:
            service.likes.add(user)
            liked = True

        return JsonResponse({'liked': liked, 'like_count': service.likes.count()})


class FlagFavouriteView(LoginRequiredMixin, View):
    def post(self, request, service_id):
        service = get_object_or_404(ServiceListing, id=service_id)
        user = request.user
        if user in service.favorite_flagged.all():
            service.favorite_flagged.remove(user)
            flagged = False
        else:
            service.favorite_flagged.add(user)
            flagged = True

        return JsonResponse({'flagged': flagged, 'flagged_count': service.favorite_flagged.count()})


class GetServiceLikersView(LoginRequiredMixin, View):
    def get(self, request, service_id):
        service = get_object_or_404(ServiceListing, id=service_id)
        likers = service.likes.all()
        data = {
            "likers": [{
                "username": user.username,
                "full_name": user.get_full_name(),
                'joined_on': user.date_joined.strftime('%B %d, %Y'),
                "profile_pic": user.profile_picture.url if user.profile_picture else None,
            } for user in likers]
        }
        return JsonResponse(data)


class DeleteServiceView(LoginRequiredMixin, DeleteView):
    model = ServiceListing
    success_url = reverse_lazy('explore_services')

    def get_queryset(self):
        return self.model.objects.filter(provider=self.request.user)


class ExtendedServiceDisplayView(LoginRequiredMixin, View):
    def get(self, request, service_id):
        service = get_object_or_404(ServiceListing.objects.prefetch_related('comments'), id=service_id)
        availability = ProviderAvailability.objects.filter(provider=service.provider).first()
        unread_count = 0

        if request.user.is_authenticated:
            unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

        time_slots = availability.time_slots.order_by('day_of_week', 'start_time') if availability else []
        time_ranges = sorted(set((slot.start_time, slot.end_time) for slot in time_slots), key=lambda r: r[0])
        slots_by_key = {
            f"{slot.day_of_week}_{slot.start_time}_{slot.end_time}": slot for slot in time_slots
        }

        context = {
            'service': service,
            'slots_by_key': slots_by_key,
            'days': WeeklyTimeSlot.DAYS_OF_WEEK,
            'time_ranges': time_ranges,
            'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY,
            'unread_count': unread_count,
        }
        return render(request, 'extended-service-display.html', context)


class ManageServiceSectionsView(LoginRequiredMixin, View):
    def get(self, request, service_id):
        service = get_object_or_404(ServiceListing, id=service_id, provider=request.user)
        availability, _ = ProviderAvailability.objects.get_or_create(provider=request.user)

        time_slots = availability.time_slots.order_by('day_of_week', 'start_time')
        time_ranges = sorted(set((slot.start_time, slot.end_time) for slot in time_slots), key=lambda r: r[0])
        slots_by_key = {
            f"{slot.day_of_week}_{slot.start_time}_{slot.end_time}": slot for slot in time_slots
        }

        availability_form = ProviderAvailabilityForm(instance=availability)
        section_formset = ServiceDetailSectionFormSet(instance=service)
        unread_count = 0

        if request.user.is_authenticated:
            unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

        return render(request, 'manage_sections_sep.html', {
            'service': service,
            'section_formset': section_formset,
            'availability_form': availability_form,
            'slots_by_key': slots_by_key,
            'days': WeeklyTimeSlot.DAYS_OF_WEEK,
            'time_ranges': time_ranges,
            'unread_count': unread_count,
        })

    def post(self, request, service_id):
        service = get_object_or_404(ServiceListing, id=service_id, provider=request.user)
        availability, _ = ProviderAvailability.objects.get_or_create(provider=request.user)

        form_type = request.POST.get('form-type')

        if form_type == 'availability-form':
            availability_form = ProviderAvailabilityForm(request.POST, instance=availability)
            if availability_form.is_valid():
                availability = availability_form.save()
                availability.time_slots.all().delete()
                availability._generate_weekly_slots()

                time_slots = availability.time_slots.order_by('day_of_week', 'start_time')
                time_ranges = sorted(set((slot.start_time, slot.end_time) for slot in time_slots), key=lambda r: r[0])
                slots_by_key = {
                    f"{slot.day_of_week}_{slot.start_time}_{slot.end_time}": slot for slot in time_slots
                }

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    table_html = render_to_string('partials/_availability_table.html', {
                        'slots_by_key': slots_by_key,
                        'days': WeeklyTimeSlot.DAYS_OF_WEEK,
                        'time_ranges': time_ranges,
                        'availability': availability
                    })
                    return JsonResponse({
                        'success': True,
                        'table_html': table_html,
                        'slot_duration': availability.slot_duration,
                        'buffer_time': availability.buffer_time
                    })

                return redirect('extended_service_display', service_id=service.id)

            elif request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': availability_form.errors}, status=400)

        elif form_type == 'sections-form':
            section_formset = ServiceDetailSectionFormSet(request.POST, request.FILES, instance=service)
            if section_formset.is_valid():
                section_formset.save()

                Notification.create_notification(
                    user=request.user,
                    title=f"Successfully added new sections to your service: {service.title}",
                    message="You can add new sections to your service as well.",
                    notification_type=NotificationType.INFO
                )
                return redirect('extended_service_display', service_id=service.id)

        return redirect('manage_service_sections', service_id=service.id)


class CommentServiceView(LoginRequiredMixin, View):
    def post(self, request, pk):
        service = get_object_or_404(
            ServiceListing.objects.prefetch_related(
                Prefetch('comments',
                         queryset=Comment.objects.select_related('author', 'parent').prefetch_related('children'))
            ),
            id=pk
        )
        form = CommentForm(request.POST)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user

            parent_id = request.POST.get('parent_id')
            if parent_id:
                try:
                    comment.parent = Comment.objects.get(id=parent_id)
                except Comment.DoesNotExist:
                    pass

            comment.save()
            service.comments.add(comment)

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                comment_html = render_to_string(
                    'partials/single-comment.html',
                    {
                        'comment': comment,
                        'service': service,
                        'parent_id': parent_id,
                    },
                    request=request
                )
                return JsonResponse({
                    'status': 'success',
                    'comment_html': comment_html,
                    'comment_id': comment.id,
                    'parent_id': parent_id,  # <- IMPORTANT!
                })

            return redirect('extended_service_display', service_id=service.id)

        return JsonResponse({'status': 'error', 'errors': form.errors})

    def get(self, request, pk):
        service = get_object_or_404(ServiceListing, id=pk)
        form = CommentForm()
        return render(request, 'partials/expand-serv-to-comment-modal.html', {
            'comments_form': form,
            'service': service
        })


class ReportContent(LoginRequiredMixin, View):
    login_url = 'login'

    def get(self, request):
        report_form = BlacklistItemForm()
        form_html = render_to_string('template-components/form-modals/report_form.html', {'report_form': report_form},
                                     request=request)
        return JsonResponse({'status': 'success', 'form_html': form_html})

    def post(self, request):
        content_type = request.POST.get('content_type')
        object_id = request.POST.get('object_id')
        reason = request.POST.get('reason')
        description = request.POST.get('description', '')

        try:
            if content_type == 'service':
                model = ServiceListing
            elif content_type == 'comment':
                model = Comment
            elif content_type == 'review':
                model = UserReview
            elif content_type == 'user':
                model = CustomUser
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid content type'}, status=400)

            content_object = model.objects.get(pk=object_id)

            # Create the report
            report = BlacklistItem.objects.create(
                reporter=request.user,
                content_object=content_object,
                reason=reason,
                description=description,
                status=BlacklistStatus.PENDING
            )

            # Auto-hide if needed based on reason
            if reason in [BlacklistReason.SCAM, BlacklistReason.ABUSE, BlacklistReason.HATE_SPEECH]:
                report.auto_hidden = True
                report.save()
                if hasattr(content_object, 'is_active'):
                    content_object.is_active = False
                    content_object.save()

            if hasattr(content_object, 'user'):
                report.check_user_ban()

            Notification.create_notification(
                user=request.user,
                title=f"Successfully submitted reported content to our admins",
                message="Thank you for making the community a safe and thriving - we will do everything we can to keep it this way!",
                notification_type=NotificationType.REPORT
            )

            return JsonResponse({
                'status': 'success',
                'message': 'Your report has been submitted. Our team will review it shortly.'
            })

        except model.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Content not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
