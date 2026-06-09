from django.core.management.base import BaseCommand
from django.db.models import Count, Max, Q

from powertracker.helpers.mm_time import get_current_myanmar_time
from powertracker.helpers.report_window import get_report_window
from powertracker.models import TownshipStatistics, UserReport


def get_snapshot_status(township, window_start, window_end, current_window_start):
    if window_end == current_window_start:
        return township.current_status

    status_counts = (
        UserReport.objects
        .filter(
            township=township,
            window_start=window_start,
            window_end=window_end,
        )
        .values("township_status")
        .annotate(status_count=Count("id"))
        .order_by("-status_count", "township_status")
    )

    if not status_counts:
        return township.current_status

    top_count = status_counts[0]["status_count"]
    top_statuses = [
        item["township_status"]
        for item in status_counts
        if item["status_count"] == top_count
    ]

    if len(top_statuses) > 1:
        return "UNCERTAIN"

    return top_statuses[0]


class Command(BaseCommand):
    help = "Process completed report windows into township statistics."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show how many statistic windows would be processed without saving.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        myanmar_now = get_current_myanmar_time()
        current_window_start, _ = get_report_window(myanmar_now)

        report_groups = (
            UserReport.objects
            .filter(window_end__lte=myanmar_now)
            .values("township", "window_start", "window_end")
            .annotate(
                reported_on_count=Count("id", filter=Q(reported_status="ON")),
                reported_off_count=Count("id", filter=Q(reported_status="OFF")),
                last_processed_report_id=Max("id"),
            )
            .order_by("window_start", "township")
        )

        processed_count = 0

        for group in report_groups:
            existing_statistic = TownshipStatistics.objects.filter(
                township_id=group["township"],
                start_time=group["window_start"],
                end_time=group["window_end"],
            ).first()

            if (
                existing_statistic
                and existing_statistic.last_processed_report_id >= group["last_processed_report_id"]
            ):
                continue

            latest_report = (
                UserReport.objects
                .select_related("township")
                .filter(
                    township_id=group["township"],
                    window_start=group["window_start"],
                    window_end=group["window_end"],
                )
                .order_by("-id")
                .first()
            )

            if latest_report is None:
                continue

            township_status = get_snapshot_status(
                latest_report.township,
                group["window_start"],
                group["window_end"],
                current_window_start,
            )

            if not dry_run:
                TownshipStatistics.objects.update_or_create(
                    township=latest_report.township,
                    start_time=group["window_start"],
                    end_time=group["window_end"],
                    defaults={
                        "township_status": township_status,
                        "reported_on_count": group["reported_on_count"],
                        "reported_off_count": group["reported_off_count"],
                        "last_processed_report_id": group["last_processed_report_id"],
                    },
                )

            processed_count += 1

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"Dry run: {processed_count} township statistic windows would be processed."
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Processed {processed_count} township statistic windows."
            )
        )
