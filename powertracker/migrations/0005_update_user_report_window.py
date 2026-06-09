from datetime import timedelta

from django.db import migrations, models


def update_existing_reports(apps, schema_editor):
    UserReport = apps.get_model("powertracker", "UserReport")

    for report in UserReport.objects.all().order_by("reported_at", "id"):
        if report.reported_status == "UP":
            report.reported_status = "ON"
        elif report.reported_status == "DOWN":
            report.reported_status = "OFF"

        window_minute = (report.reported_at.minute // 5) * 5
        report.window_start = report.reported_at.replace(
            minute=window_minute,
            second=0,
            microsecond=0
        )
        report.window_end = report.window_start + timedelta(minutes=5)
        report.save(update_fields=[
            "reported_status",
            "window_start",
            "window_end",
        ])

    duplicate_groups = (
        UserReport.objects
        .values("user_id", "township_id", "window_start")
        .annotate(report_count=models.Count("id"))
        .filter(report_count__gt=1)
    )

    for group in duplicate_groups:
        reports = UserReport.objects.filter(
            user_id=group["user_id"],
            township_id=group["township_id"],
            window_start=group["window_start"],
        ).order_by("-reported_at", "-id")

        reports.exclude(id=reports.first().id).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("powertracker", "0004_favoritetownship_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="userreport",
            old_name="vote",
            new_name="reported_status",
        ),
        migrations.AddField(
            model_name="userreport",
            name="window_start",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="userreport",
            name="window_end",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="userreport",
            name="reported_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.RunPython(update_existing_reports, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="userreport",
            name="reported_status",
            field=models.CharField(
                choices=[("ON", "ON"), ("OFF", "OFF")],
                max_length=3,
            ),
        ),
        migrations.AlterField(
            model_name="userreport",
            name="window_start",
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name="userreport",
            name="window_end",
            field=models.DateTimeField(),
        ),
        migrations.AddConstraint(
            model_name="userreport",
            constraint=models.UniqueConstraint(
                fields=("user", "township", "window_start"),
                name="unique_user_township_report_window",
            ),
        ),
        migrations.AddIndex(
            model_name="userreport",
            index=models.Index(
                fields=["window_start"],
                name="powertracke_window__c8b893_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="userreport",
            index=models.Index(
                fields=["township", "window_start"],
                name="powertracke_townsh_7e51f7_idx",
            ),
        ),
    ]
