from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views import View
from JobJab.core.forms import CertificateForm
from JobJab.core.models import CustomUser, Certificate, Notification, NotificationType


class UserCertificatesView(LoginRequiredMixin, View):
    def get(self, request, username):
        user = get_object_or_404(CustomUser, username=username)
        unread_count = 0

        if request.user.is_authenticated:
            unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

        form = CertificateForm()
        certificates = Certificate.objects.filter(user=user)
        return render(request, 'core/accounts/account-tabs/account_certificates.html', {
            'user': user,
            'certificates': certificates,
            'form': form,
            'unread_count': unread_count,
        })

    def post(self, request, username):
        user = get_object_or_404(CustomUser, username=username)
        form = CertificateForm(request.POST, request.FILES)
        if form.is_valid():
            cert = form.save(commit=False)
            cert.user = request.user
            cert.save()

            Notification.create_notification(
                user=user,
                title="Successful Certificate Upload",
                message="You have created a new certificate. Make sure it is seen - service candidates are around the corner!",
                notification_type=NotificationType.INFO
            )

            return redirect('user_certificates', username=username)
        certificates = Certificate.objects.filter(user=user)
        return render(request, 'core/accounts/account-tabs/account_certificates.html', {
            'user': user,
            'certificates': certificates,
            'form': form
        })


class EditCertificateView(LoginRequiredMixin, View):
    def get(self, request, certificate_id):
        certificate = get_object_or_404(Certificate, pk=certificate_id)
        form = CertificateForm(instance=certificate)
        form_html = render_to_string('template-components/form-modals/edit-certificate-form.html', {
            'form': form,
            'certificate_id': certificate_id
        }, request=request)
        return JsonResponse({'form_html': form_html})

    def post(self, request, certificate_id):
        certificate = get_object_or_404(Certificate, pk=certificate_id)
        form = CertificateForm(request.POST, request.FILES, instance=certificate)
        if form.is_valid():
            form.save()

            Notification.create_notification(
                user=request.user,
                title="Successful Certificate Edit",
                message=f"You have successfully edited certificate {certificate.title}",
                notification_type=NotificationType.INFO
            )

            return JsonResponse(
                {'success': True, 'redirect_url': reverse_lazy('user_certificates', args=[request.user.username])})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)


class DeleteCertificateView(LoginRequiredMixin, View):
    def post(self, request, cert_id):
        certificate = get_object_or_404(Certificate, id=cert_id)
        if request.user == certificate.user:
            certificate.delete()
            Notification.create_notification(
                user=request.user,
                title=f"Successfully deleted certificate {certificate.title}",
                message="We have detected that a certificate has been removed from your account recently!",
                notification_type=NotificationType.INFO
            )

        return redirect('user_certificates', username=request.user.username)
