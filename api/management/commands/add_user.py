from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create or update a Django user for OIDC login only (no password)'

    def handle(self, *args, **options):
        print("🧑 Add or update an OIDC-only Django user")

        email = input("Email: ").strip()
        username = input("Username: ").strip()
        first_name = input("First name: ").strip()
        last_name = input("Last name: ").strip()

        is_staff = input("Is staff user? (y/N): ").strip().lower() == 'y'
        is_superuser = input("Is superuser? (y/N): ").strip().lower() == 'y'

        user, created = User.objects.update_or_create(
            email=email,
            defaults={
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "is_staff": is_staff,
                "is_superuser": is_superuser,
            }
        )

        user.set_unusable_password()
        user.save()

        status = "✅ Created" if created else "✅ Updated"
        self.stdout.write(f"{status} OIDC-only user: {username} ({email})")