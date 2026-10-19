import datetime
from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from certificates.models import Certificate


class Command(BaseCommand):
    help = (
        "Send email reminders to business owners whose instrument verification certificates "
        "expire in exactly 30 and 7 days."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simulate execution without sending actual emails.",
        )
        parser.add_argument(
            "--days",
            nargs="+",
            type=int,
            default=[30, 7],
            help="Days before expiry to trigger reminders (default: 30 7).",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        reminder_days = options["days"]
        today = timezone.now().date()

        target_dates = [today + datetime.timedelta(days=d) for d in reminder_days]
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"\nChecking certificate expiry reminders for {today} (thresholds: {reminder_days} days)..."
            )
        )

        certs = (
            Certificate.objects.filter(
                valid_until__in=target_dates,
                revoked_at__isnull=True,
            )
            .select_related(
                "inspection__request__instrument__business__owner",
                "inspection__request__instrument",
            )
            .order_by("valid_until")
        )

        total_found = certs.count()
        if total_found == 0:
            self.stdout.write(self.style.SUCCESS("No certificates due for 30-day or 7-day expiry reminder today.\n"))
            return

        self.stdout.write(f"Found {total_found} certificate(s) qualifying for expiry reminders.\n")

        sent_count = 0
        site_url = getattr(settings, "SITE_URL", "http://localhost:8000").rstrip("/")
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "compliance@tola.local")

        for cert in certs:
            instrument = cert.inspection.request.instrument
            business = instrument.business
            owner = business.owner
            days_left = (cert.valid_until - today).days

            owner_name = owner.get_full_name() or owner.username
            recipient_email = owner.email

            if not recipient_email:
                self.stdout.write(
                    self.style.WARNING(
                        f"  [SKIPPED] Cert #{cert.number} ({instrument.serial_no}) - Owner {owner.username} has no email."
                    )
                )
                continue

            subject = f"Statutory Notice: Verification Certificate #{cert.number} expires in {days_left} days"
            message = (
                f"Dear {owner_name},\n\n"
                f"This is an official statutory reminder under the Legal Metrology Act, 2009.\n\n"
                f"Your Legal Metrology Verification Certificate #{cert.number} for:\n"
                f"  - Instrument: {instrument.get_category_display()} ({instrument.make} {instrument.model_no})\n"
                f"  - Serial Number: {instrument.serial_no}\n"
                f"  - Business: {business.name} ({business.district})\n\n"
                f"is scheduled to EXPIRE in {days_left} days on {cert.valid_until.strftime('%d %B %Y')}.\n\n"
                f"To ensure uninterrupted legal trade and compliance under Section 24 of the Legal Metrology Act, "
                f"please submit a verification renewal request through the online portal:\n\n"
                f"Renewal Filing URL:\n"
                f"{site_url}/app/requests/new/?instrument={instrument.pk}\n\n"
                f"Public Verification Ledger Record:\n"
                f"{site_url}/v/{cert.token}/\n\n"
                f"Controller of Legal Metrology\n"
                f"Tola Online Verification Desk\n"
            )

            if dry_run:
                self.stdout.write(
                    f"  [DRY RUN] Would send {days_left}d reminder for Cert #{cert.number} to {recipient_email}"
                )
                sent_count += 1
            else:
                try:
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=from_email,
                        recipient_list=[recipient_email],
                        fail_silently=False,
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  [SENT] {days_left}d reminder for Cert #{cert.number} sent to {recipient_email}"
                        )
                    )
                    sent_count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"  [ERROR] Failed to send email for Cert #{cert.number} to {recipient_email}: {e}"
                        )
                    )

        action_word = "Simulated" if dry_run else "Dispatched"
        self.stdout.write(
            self.style.SUCCESS(f"\n{action_word} {sent_count} certificate expiry reminder(s) successfully.\n")
        )
