from django.contrib import admin

from .models import Subscriber, Visit


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('email',)
    search_fields = ('email',)


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ('path', 'created_at', 'visit_day')
    list_filter = ('visit_day', 'path')
    search_fields = ('path', 'visitor_fingerprint', 'ip_hash')
    readonly_fields = (
        'path',
        'visitor_fingerprint',
        'ip_hash',
        'user_agent_hash',
        'referrer',
        'created_at',
        'visit_day',
    )
