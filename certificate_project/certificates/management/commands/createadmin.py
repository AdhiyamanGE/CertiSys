from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Create admin user"

    def handle(self, *args, **options):
        admin_username = input("Enter admin username:")
        admin_email = input("Enter admin email:")
        admin_password = input("Enter admin password:")

        if not User.objects.filter(username=admin_username).exists():
            User.objects.create_superuser(
                username=admin_username, email=admin_email, password=admin_password
            )
            self.stdout.write(self.style.SUCCESS("Admin user created successfully."))
        else:
            self.stdout.write(self.style.WARNING("Admin user already exists."))
