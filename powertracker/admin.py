from django.contrib import admin

from .models import Schedule, Township, TownshipStatistics, UserProfile, UserReport


admin.site.register(Township)
admin.site.register(UserProfile)
admin.site.register(UserReport)
admin.site.register(TownshipStatistics)
admin.site.register(Schedule)
