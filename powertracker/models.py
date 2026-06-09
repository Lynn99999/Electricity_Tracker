from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import get_language

class Township(models.Model):

    GROUP_CHOICES = [
        ("A", "Group A"),
        ("B", "Group B"),
        
    ]

    STATUS_CHOICES = [
        ("ON", "Electricity ON"),
        ("OFF", "Electricity OFF"),
        ("UNCERTAIN", "Uncertain"),
    ]
    
    name = models.CharField(
        max_length=100, unique=True
        )
    name_mm = models.CharField(
        max_length=100, blank=True
        )
    name_zh = models.CharField(
        max_length=100, blank=True
        )


    group = models.CharField(
        max_length=1,
        choices=GROUP_CHOICES
    )

    current_status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="UNCERTAIN"
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name

    @property
    def localized_name(self):
        language = (get_language() or "en").lower()

        if language.startswith("my") and self.name_mm:
            return self.name_mm

        if language.startswith("zh") and self.name_zh:
            return self.name_zh

        return self.name

class UserProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    favorite_townships = models.ManyToManyField(
        "Township",
        through="FavoriteTownship",
        blank=True
    )

    def __str__(self):
        return self.user.username

class UserReport(models.Model):

    STATUS_CHOICES = [
        ("ON", "ON"),
        ("OFF", "OFF"),
        ("UNCERTAIN", "UNCERTAIN"),
    ]

    REPORTED_STATUS_CHOICES = [
        ("ON", "ON"),
        ("OFF", "OFF"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    township = models.ForeignKey(
        Township,
        on_delete=models.CASCADE
    )

    township_status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES
    )

    reported_status = models.CharField(
        max_length=3,
        choices=REPORTED_STATUS_CHOICES
    )

    window_start = models.DateTimeField()

    window_end = models.DateTimeField()

    reported_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "township", "window_start"],
                name="unique_user_township_report_window"
            )
        ]

        indexes = [
            models.Index(fields=["window_start"]),
            models.Index(fields=["township", "window_start"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.township.name}"

class TownshipStatistics(models.Model):

    STATUS_CHOICES = [
        ("ON", "ON"),
        ("OFF", "OFF"),
        ("UNCERTAIN", "UNCERTAIN"),
    ]

    township = models.ForeignKey(
        Township,
        on_delete=models.CASCADE
    )

    township_status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES
    )

    reported_on_count = models.PositiveIntegerField(
        default=0
    )

    reported_off_count = models.PositiveIntegerField(
        default=0
    )

    start_time = models.DateTimeField()

    end_time = models.DateTimeField()

    last_processed_report_id = models.PositiveBigIntegerField(
    default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"{self.township.name} "
            f"({self.start_time} - {self.end_time})"
        )

class Schedule(models.Model):

    STATUS_CHOICES = [
        ("A", "Group A"),
        ("B", "Group B"),
        ("All", "Group A and B"),
    ]

    date = models.DateField()

    start_time = models.TimeField()

    end_time = models.TimeField()

    active_group = models.CharField(
        max_length=3,
        choices=STATUS_CHOICES
    )

    def __str__(self):
        return (
            f"{self.date} "
            f"{self.start_time}-{self.end_time}"
        )

class FavoriteTownship(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    township = models.ForeignKey(Township, on_delete=models.CASCADE)
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["position", "created_at"]
        unique_together = ["user_profile", "township"]

    def __str__(self):
        return f"{self.user_profile.user.username} - {self.township.name}"


class ContactMessage(models.Model):

    CATEGORY_CHOICES = [
        ("STATUS", "Wrong electricity status"),
        ("SCHEDULE", "Schedule data issue"),
        ("ACCOUNT", "Account or login issue"),
        ("FEEDBACK", "Feedback"),
        ("OTHER", "Other"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    township = models.ForeignKey(
        Township,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    name = models.CharField(max_length=120)

    email = models.EmailField()

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES
    )

    message = models.TextField()

    is_resolved = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category", "is_resolved"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.get_category_display()} - {self.email}"


class UserPushSubscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="push_subscriptions",
    )

    endpoint = models.URLField(unique=True)

    p256dh = models.TextField()

    auth = models.TextField()

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self):
        return f"{self.user.username} push subscription"


class ScheduleNotification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="schedule_notifications",
    )

    township = models.ForeignKey(
        Township,
        on_delete=models.CASCADE,
    )

    schedule = models.ForeignKey(
        Schedule,
        on_delete=models.CASCADE,
    )

    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "township", "schedule"],
                name="unique_user_township_schedule_notification",
            )
        ]
        indexes = [
            models.Index(fields=["user", "sent_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.township.name} - {self.schedule}"
