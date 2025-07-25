from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import TemplateView, DeleteView
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.db.models import Q

from JobJab.services.models import ServiceListing, Comment
from .forms import ServiceListingForm, ServiceDetailSectionFormSet, CommentForm
from .utils import get_service_limit_for_plan
from ..booking.forms import ProviderAvailabilityForm
from ..booking.models import ProviderAvailability, WeeklyTimeSlot
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
            }
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

        return render(request, 'manage_sections_sep.html', {
            'service': service,
            'section_formset': section_formset,
            'availability_form': availability_form,
            'slots_by_key': slots_by_key,
            'days': WeeklyTimeSlot.DAYS_OF_WEEK,
            'time_ranges': time_ranges,
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
                return redirect('extended_service_display', service_id=service.id)

        return redirect('manage_service_sections', service_id=service.id)


class CommentServiceView(LoginRequiredMixin, View):
    def post(self, request, pk):
        service = get_object_or_404(ServiceListing, id=pk)
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

            redirect_url = reverse('extended_service_display', args=[service.id]) + f'#comment-{comment.id}'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success', 'redirect_url': redirect_url, 'comment_id': comment.id})
            return redirect(redirect_url)

        return render(request, 'partials/expand-serv-to-comment-modal.html', {
            'comments_form': form,
            'service': service
        })

    def get(self, request, pk):
        service = get_object_or_404(ServiceListing, id=pk)
        form = CommentForm()
        return render(request, 'partials/expand-serv-to-comment-modal.html', {
            'comments_form': form,
            'service': service
        })
