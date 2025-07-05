from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
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


@login_required
def delete_certificate(request, pk):
    certificate = get_object_or_404(Certificate, pk=pk)
    if request.user == certificate.user:
        certificate.delete()
    return redirect('user_certificates', username=request.user.username)