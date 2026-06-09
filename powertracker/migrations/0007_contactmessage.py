from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("powertracker", "0006_rename_township_statistics_counts"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ContactMessage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(max_length=120),
                ),
                (
                    "email",
                    models.EmailField(max_length=254),
                ),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("STATUS", "Wrong electricity status"),
                            ("SCHEDULE", "Schedule data issue"),
                            ("ACCOUNT", "Account or login issue"),
                            ("FEEDBACK", "Feedback"),
                            ("OTHER", "Other"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "message",
                    models.TextField(),
                ),
                (
                    "is_resolved",
                    models.BooleanField(default=False),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "township",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="powertracker.township",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="contactmessage",
            index=models.Index(
                fields=["category", "is_resolved"],
                name="powertracke_categor_91ce50_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="contactmessage",
            index=models.Index(
                fields=["created_at"],
                name="powertracke_created_7c306d_idx",
            ),
        ),
    ]
