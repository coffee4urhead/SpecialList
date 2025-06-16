import uuid
from django.core.management.base import BaseCommand
from JobJab.core.models import Organization


class Command(BaseCommand):
    help = 'Creates test organizations'

    def handle(self, *args, **options):
        test_orgs_data = {
            'BMW': 'https://www.bmw.com/en/index.html',
            'NAVI': 'https://navi.gg/en',
            'Facebook': 'https://www.facebook.com/',
            'Google': 'https://www.google.com/',
            'WWE': 'https://www.wwe.com/',
        }

        for name, url in test_orgs_data.items():
            org, created = Organization.objects.get_or_create(
                name=name,
                defaults={'website': url}
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created organization: {org.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠️ Organization already exists: {org.name}'))
