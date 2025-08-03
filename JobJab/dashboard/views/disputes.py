from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.http import JsonResponse
from django.views import View

from JobJab.core.models import BlacklistItem, Notification, NotificationType


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