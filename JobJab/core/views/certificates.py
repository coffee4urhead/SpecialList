from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.clickjacking import xframe_options_sameorigin
from JobJab.core.forms import CertificateForm
from JobJab.core.models import CustomUser, Certificate

@login_required
@xframe_options_sameorigin
def user_certificates(request, username):
    user = get_object_or_404(CustomUser, username=username)

    if request.method == 'POST':
        form = CertificateForm(request.POST, request.FILES)
        if form.is_valid():
            certificate = form.save(commit=False)
            certificate.user = request.user
            certificate.save()
            return redirect('user_certificates', username=username)
    else:
        form = CertificateForm()

    certificates = Certificate.objects.filter(user=user)
    return render(request, 'core/accounts/account-tabs/account_certificates.html', {
        'user': user,
        'certificates': certificates,
        'form': form
    })


@login_required(login_url='login')
def edit_certificate(request, certificate_id):
    certificate = get_object_or_404(Certificate, pk=certificate_id)

    if request.method == 'POST':
        form = CertificateForm(request.POST, request.FILES, instance=certificate)
        if form.is_valid():
            form.save()
            return JsonResponse(
                {'success': True, 'redirect_url': reverse('user_certificates', args=[request.user.username])})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    else:
        form = CertificateForm(instance=certificate)

        form_html = render_to_string('template-components/form-modals/edit-certificate-form.html', {
            'form': form,
            'certificate_id': certificate_id
        }, request=request)
        return JsonResponse({'form_html': form_html})

@login_required
def delete_certificate(request, cert_id):
    certificate = get_object_or_404(Certificate, id=cert_id)
    if request.user == certificate.user:
        certificate.delete()
    return redirect('user_certificates', username=request.user.username)