from django.contrib import admin
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin

from .models import (
    ContactMessage,
    FavoriteTownship,
    Schedule,
    ScheduleNotification,
    Township,
    TownshipStatistics,
    UserProfile,
    UserPushSubscription,
    UserReport,
)


class TownshipResource(resources.ModelResource):
    name = fields.Field(attribute="name", column_name="English")
    name_mm = fields.Field(attribute="name_mm", column_name="Burmese")
    name_zh = fields.Field(attribute="name_zh", column_name="Chinese")
    group = fields.Field(attribute="group", column_name="Group")

    class Meta:
        model = Township
        fields = ("name", "name_mm", "name_zh", "group")
        import_id_fields = ("name",)
        skip_unchanged = True
        report_skipped = True


@admin.register(Township)
class TownshipAdmin(ImportExportModelAdmin):
    resource_class = TownshipResource
    list_display = ("name", "name_mm", "name_zh", "group", "current_status")
    list_filter = ("group", "current_status")
    search_fields = ("name", "name_mm", "name_zh")

class ScheduleResource(resources.ModelResource):
    date = fields.Field(attribute="date", column_name="date")
    start_time = fields.Field(attribute="start_time", column_name="start_time")
    end_time = fields.Field(attribute="end_time", column_name="end_time")
    active_group = fields.Field(attribute="active_group", column_name="active_group")

    class Meta:
        model = Schedule
        fields = ("date", "start_time", "end_time", "active_group")
        import_id_fields = ("date", "start_time", "end_time")
        skip_unchanged = True
        report_skipped = True


@admin.register(Schedule)
class ScheduleAdmin(ImportExportModelAdmin):
    resource_class = ScheduleResource
    list_display = ("date", "start_time", "end_time", "active_group")
    list_filter = ("date", "active_group")

admin.site.register(UserProfile)
admin.site.register(FavoriteTownship)
@admin.register(UserReport)
class UserReportAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "township",
        "township_status",
        "reported_status",
        "window_start",
        "window_end",
        "reported_at",
    )
    list_filter = ("reported_status", "township_status", "window_start")
    search_fields = ("user__username", "township__name")
    ordering = ("-reported_at",)


admin.site.register(TownshipStatistics)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "category",
        "name",
        "email",
        "township",
        "is_resolved",
    )
    list_filter = ("category", "is_resolved", "created_at")
    search_fields = ("name", "email", "message", "township__name", "user__username")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)


@admin.register(UserPushSubscription)
class UserPushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "is_active", "created_at", "updated_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("user__username", "endpoint")
    readonly_fields = ("created_at", "updated_at")


@admin.register(ScheduleNotification)
class ScheduleNotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "township", "schedule", "sent_at")
    list_filter = ("sent_at", "township")
    search_fields = ("user__username", "township__name")
    readonly_fields = ("sent_at",)
