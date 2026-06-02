from django.db import models
from django.contrib.auth.models import User

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
        max_length=100,
        unique=True
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

class UserProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    correct_rate = models.FloatField(
        default=100.0
    )

    report_count = models.PositiveIntegerField(
        default=0
    )

    favorite_townships = models.ManyToManyField(
        "Township",
        blank=True
    )

    is_verified = models.BooleanField(
    default=False
)

    def __str__(self):
        return self.user.username

class UserReport(models.Model):

    STATUS_CHOICES = [
        ("ON", "ON"),
        ("OFF", "OFF"),
        ("UNCERTAIN", "UNCERTAIN"),
    ]

    VOTE_CHOICES = [
        ("UP", "Thumb Up"),
        ("DOWN", "Thumb Down"),
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

    vote = models.CharField(
        max_length=4,
        choices=VOTE_CHOICES
    )

    reported_at = models.DateTimeField(
        auto_now_add=True
    )

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

    thumb_up_count = models.PositiveIntegerField(
        default=0
    )

    thumb_down_count = models.PositiveIntegerField(
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
        ("A+B", "Group A and B"),
        ("B+A", "Group B and A"),
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
