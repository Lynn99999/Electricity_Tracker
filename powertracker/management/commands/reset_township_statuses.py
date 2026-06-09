from django.core.management.base import BaseCommand

from powertracker.helpers.check_status import update_township_statuses
from powertracker.models import Township


class Command(BaseCommand):
    help = "Reset township current statuses to the current schedule."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show township status changes without saving.",
        )

    def handle(self, *args, **options):
        if not options["dry_run"]:
            update_township_statuses()
            self.stdout.write(
                self.style.SUCCESS("Township statuses were reset to the current schedule.")
            )
            return

        township_changes = []

        from powertracker.helpers.check_status import (
            get_current_schedule,
            get_expected_status_for_township,
        )

        current_schedule = get_current_schedule()

        for township in Township.objects.all().order_by("name"):
            expected_status = get_expected_status_for_township(
                township,
                current_schedule,
            )

            if township.current_status != expected_status:
                township_changes.append(
                    f"{township.name}: {township.current_status} -> {expected_status}"
                )

        if not township_changes:
            self.stdout.write("No township status changes needed.")
            return

        self.stdout.write(
            self.style.WARNING(
                f"{len(township_changes)} township statuses would change:"
            )
        )

        for change in township_changes:
            self.stdout.write(change)
