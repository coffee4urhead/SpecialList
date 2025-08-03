from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.http import JsonResponse
from django.views import View

from JobJab.core.models import BlacklistItem, Notification, NotificationType
from JobJab.services.models import DeletedService


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
            content_obj = dispute.content_object

            if action == 'approve':
                dispute.approve_report(moderator=request.user)

                if dispute.content_type.model == 'servicelisting' and content_obj:
                    content_obj.deactivate_service(user=request.user, reason=dispute.get_reason_display(), is_deleted=True)


                    service_data = {
                        "provider_id": content_obj.provider_id,
                        "title": content_obj.title,
                        "description": content_obj.description,
                        "location": content_obj.location,
                        "category": content_obj.category,
                        "price": str(content_obj.price),
                        "duration_minutes": content_obj.duration_minutes,
                        "created_at": content_obj.created_at.isoformat(),
                        "updated_at": content_obj.updated_at.isoformat(),
                    }

                    DeletedService.objects.create(
                        service_data=service_data,
                        deleted_by=request.user
                    )

                Notification.create_notification(
                    user=dispute.reporter,
                    title="Successfully approved your report!",
                    message="Thank you for your report. Make sure the community remains safe and threat free!",
                    notification_type=NotificationType.BAN
                )

                # Notify owner of content if applicable
                if hasattr(content_obj, 'user') and content_obj.user != dispute.reporter:
                    Notification.objects.create(
                        user=content_obj.user,
                        title="Content Violation",
                        message=f"Your {dispute.content_type.model} was removed for violating our policies",
                        notification_type=NotificationType.WARNING
                    )

            elif action == 'reject':
                dispute.reject_report(moderator=request.user)
                Notification.create_notification(
                    user=dispute.reporter,
                    title="Your report has been rejected!",
                    message="Keep in mind that any future false reports may result in bans to your account. Be mindful what you report and for what reason - everything is reviewed by our admins!",
                    notification_type=NotificationType.WARNING
                )
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid action'}, status=400)

            return JsonResponse({'status': 'success'})

        except BlacklistItem.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Dispute not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
