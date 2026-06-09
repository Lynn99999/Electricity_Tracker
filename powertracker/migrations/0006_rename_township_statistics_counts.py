from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("powertracker", "0005_update_user_report_window"),
    ]

    operations = [
        migrations.RenameField(
            model_name="townshipstatistics",
            old_name="thumb_up_count",
            new_name="reported_on_count",
        ),
        migrations.RenameField(
            model_name="townshipstatistics",
            old_name="thumb_down_count",
            new_name="reported_off_count",
        ),
    ]
