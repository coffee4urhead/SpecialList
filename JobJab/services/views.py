from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from JobJab.services.models import ServiceListing, Comment
from .forms import ServiceListingForm, ServiceDetailSectionFormSet, CommentForm
from ..booking.forms import ProviderAvailabilityForm
from ..booking.models import ProviderAvailability

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']


@login_required
def explore_services(request):
    availability, _ = ProviderAvailability.objects.get_or_create(provider=request.user)

    if request.method == 'POST':
        form = ProviderAvailabilityForm(request.POST, instance=availability)
        if form.is_valid():
            form.save()

            availability.time_slots.all().delete()
            availability._generate_weekly_slots()

            return redirect('explore_services')
    else:
        form = ProviderAvailabilityForm(instance=availability)

    time_slots = availability.time_slots.order_by('day_of_week', 'start_time')

    return render(request, 'explore_services.html', {
        'form': ServiceListingForm(),
        'availability_form': form,
        'time_slots': time_slots,
        'services': ServiceListing.objects.all()
    })


@login_required(login_url='login')
def like_service(request, service_id):
    service = get_object_or_404(ServiceListing, id=service_id)
    user = request.user

    if request.method == 'POST':
        if user in service.likes.all():
            service.likes.remove(user)
            liked = False
        else:
            service.likes.add(user)
            liked = True

        return JsonResponse({
            'liked': liked,
            'like_count': service.likes.count()
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required(login_url='login')
def flag_favourite(request, service_id):
    service = get_object_or_404(ServiceListing, id=service_id)
    user = request.user

    if request.method == 'POST':
        if user in service.favorite_flagged.all():
            service.favorite_flagged.remove(user)
            flagged = False
        else:
            service.favorite_flagged.add(user)
            flagged = True

        return JsonResponse({
            'flagged': flagged,
            'flagged_count': service.favorite_flagged.count()
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def get_service_likers(request, service_id):
    service = get_object_or_404(ServiceListing, id=service_id)
    likers = service.likes.all()

    data = {
        "likers": [
            {
                "username": user.username,
                "full_name": user.get_full_name(),
                'joined_on': user.date_joined.strftime('%B %d, %Y'),
                "profile_pic": user.profile_picture.url if user.profile_picture else None,
            } for user in likers
        ]
    }
    return JsonResponse(data)


@login_required
def delete_service(request, pk):
    service = get_object_or_404(ServiceListing, pk=pk)
    if request.user == service.provider:
        service.delete()
    return redirect('explore_services')


@login_required
def extended_service_display(request, service_id):
    service = get_object_or_404(ServiceListing.objects.prefetch_related('comments'), id=service_id)
    return render(request, 'extended-service-display.html', {'service': service})


@login_required
def manage_service_sections(request, service_id):
    service = get_object_or_404(ServiceListing, id=service_id, provider=request.user)

    if request.method == 'POST':
        formset = ServiceDetailSectionFormSet(request.POST, request.FILES, instance=service)
        if formset.is_valid():
            formset.save()
            return redirect('extended_service_display', service_id=service.id)

        print("Formset errors:", formset.errors)
    else:
        formset = ServiceDetailSectionFormSet(instance=service)

    return render(request, 'manage_sections_sep.html', {
        'service': service,
        'formset': formset
    })


@login_required(login_url='login')
def comment_service(request, pk):
    service = get_object_or_404(ServiceListing, id=pk)

    if request.method == 'POST':
        comments_form = CommentForm(request.POST)
        if comments_form.is_valid():
            comment = comments_form.save(commit=False)
            comment.author = request.user

            parent_id = request.POST.get('parent_id')
            if parent_id:
                try:
                    parent_comment = Comment.objects.get(id=parent_id)
                    comment.parent = parent_comment
                except Comment.DoesNotExist:
                    print("Comment doesn't exist")

            comment.save()
            print(f"Comment saved {comment}")
            service.comments.add(comment)

            redirect_url = reverse('extended_service_display', args=[service.id]) + f'#comment-{comment.id}'

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'redirect_url': redirect_url,
                    'comment_id': comment.id
                })

            return redirect(redirect_url)

    comments_form = CommentForm()
    return render(request, 'partials/expand-serv-to-comment-modal.html', {
        'comments_form': comments_form,
        'service': service
    })
