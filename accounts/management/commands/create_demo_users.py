from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Creates one admin, one inspector, and two business owners with printed credentials."

    def handle(self, *args, **options):
        demo_users = [
            {
                "username": "admin",
                "email": "admin@tola.local",
                "password": "AdminPassword123!",
                "role": User.Role.ADMIN,
                "phone": "+91 90000 00001",
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "username": "inspector_rajesh",
                "email": "rajesh.inspector@tola.local",
                "password": "InspectorPassword123!",
                "role": User.Role.INSPECTOR,
                "phone": "+91 98765 43210",
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "username": "owner_ramesh",
                "email": "ramesh.grocers@tola.local",
                "password": "OwnerPassword123!",
                "role": User.Role.OWNER,
                "phone": "+91 98765 43211",
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "username": "owner_priya",
                "email": "priya.jewellers@tola.local",
                "password": "OwnerPassword123!",
                "role": User.Role.OWNER,
                "phone": "+91 98765 43212",
                "is_staff": False,
                "is_superuser": False,
            },
        ]

        self.stdout.write(self.style.MIGRATE_HEADING("\n--- Tola Demo Users ---"))
        self.stdout.write(f"{'Role':<12} | {'Username':<18} | {'Password':<22} | {'Phone':<16}")
        self.stdout.write("-" * 75)

        for user_data in demo_users:
            user, created = User.objects.get_or_create(
                username=user_data["username"],
                defaults={
                    "email": user_data["email"],
                    "role": user_data["role"],
                    "phone": user_data["phone"],
                    "is_staff": user_data["is_staff"],
                    "is_superuser": user_data["is_superuser"],
                },
            )
            # Update password and attributes to keep idempotent
            user.set_password(user_data["password"])
            user.role = user_data["role"]
            user.phone = user_data["phone"]
            user.email = user_data["email"]
            user.is_staff = user_data["is_staff"]
            user.is_superuser = user_data["is_superuser"]
            user.save()

            status = "created" if created else "updated"
            self.stdout.write(
                f"{user.get_role_display():<12} | {user.username:<18} | {user_data['password']:<22} | {user.phone:<16} ({status})"
            )

        self.stdout.write("-" * 75)
        self.stdout.write(self.style.SUCCESS("All demo users are ready to log in.\n"))
