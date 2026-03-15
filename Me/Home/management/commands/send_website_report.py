from collections import Counter
from datetime import timedelta
import socket
import subprocess
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from Home.models import Visit


class Command(BaseCommand):
    help = 'Send an email report with website uptime and visitor statistics.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Number of trailing hours to include in the visitor stats window.',
        )
        parser.add_argument(
            '--retention-days',
            type=int,
            default=getattr(settings, 'VISIT_RETENTION_DAYS', 180),
            help='Delete visit records older than this many days before sending the report.',
        )

    def handle(self, *args, **options):
        recipients = getattr(settings, 'REPORT_EMAIL_TO', [])
        if not recipients:
            raise CommandError('REPORT_EMAIL_TO is not configured.')

        window_hours = options['hours']
        retention_days = options['retention_days']
        deleted_visits = self.prune_old_visits(retention_days)
        since = timezone.now() - timedelta(hours=window_hours)
        visits = Visit.objects.filter(created_at__gte=since)

        page_views = visits.count()
        unique_visitors = visits.values('visitor_fingerprint').distinct().count()
        top_paths = Counter(visits.values_list('path', flat=True)).most_common(5)
        service_statuses = self.handle_service_statuses()
        public_check = self.check_url('Public site', settings.SITE_PUBLIC_URL)
        local_check = self.check_url('Local origin', settings.SITE_LOCAL_URL, host_header='williamspalding.com')

        subject = f"Personal Website Report - {timezone.localtime().strftime('%Y-%m-%d %H:%M %Z')}"
        body = self.render_body(
            window_hours=window_hours,
            page_views=page_views,
            unique_visitors=unique_visitors,
            top_paths=top_paths,
            deleted_visits=deleted_visits,
            retention_days=retention_days,
            service_statuses=service_statuses,
            public_check=public_check,
            local_check=local_check,
        )

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=getattr(settings, 'REPORT_EMAIL_FROM', settings.DEFAULT_FROM_EMAIL),
            to=recipients,
        )
        email.send(fail_silently=False)
        self.stdout.write(self.style.SUCCESS(f'Sent website report to {", ".join(recipients)}'))

    def render_body(self, **context):
        uptime = self.read_uptime()
        hostname = socket.gethostname()
        lines = [
            f"Website report for {hostname}",
            '',
            f"Server uptime: {uptime}",
            '',
            'HTTP checks:',
            f"- {context['public_check']['label']}: {context['public_check']['status']} ({context['public_check']['url']})",
            f"- {context['local_check']['label']}: {context['local_check']['status']} ({context['local_check']['url']})",
            '',
            'Service states:',
        ]

        for service, status in context['service_statuses'].items():
            lines.append(f"- {service}: {status}")

        lines.extend([
            '',
            f"Page views (last {context['window_hours']} hours): {context['page_views']}",
            f"Unique visitors (last {context['window_hours']} hours): {context['unique_visitors']}",
            f"Old visit records pruned: {context['deleted_visits']} (retention: {context['retention_days']} days)",
            '',
            'Top paths:',
        ])

        if context['top_paths']:
            for path, count in context['top_paths']:
                lines.append(f"- {path}: {count}")
        else:
            lines.append('- No visits recorded in this window')

        return '\n'.join(lines)

    @staticmethod
    def read_uptime():
        try:
            with open('/proc/uptime', 'r', encoding='utf-8') as uptime_file:
                uptime_seconds = int(float(uptime_file.read().split()[0]))
        except (FileNotFoundError, OSError, ValueError):
            return 'Unavailable'

        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60
        return f'{days} days, {hours} hours, {minutes} minutes'

    @staticmethod
    def handle_service_statuses():
        statuses = {}
        for service in ('nginx', 'daphne', 'cloudflared'):
            result = subprocess.run(
                ['systemctl', 'is-active', service],
                capture_output=True,
                text=True,
                check=False,
            )
            statuses[service] = result.stdout.strip() or result.stderr.strip() or 'unknown'
        return statuses

    @staticmethod
    def prune_old_visits(retention_days):
        cutoff = timezone.now() - timedelta(days=retention_days)
        deleted_count, _ = Visit.objects.filter(created_at__lt=cutoff).delete()
        return deleted_count

    @staticmethod
    def check_url(label, url, host_header=None):
        request = Request(url, headers={'User-Agent': 'website-report/1.0'})
        if host_header:
            request.add_header('Host', host_header)

        try:
            with urlopen(request, timeout=10) as response:
                status = f'{response.status} {response.reason}'
        except HTTPError as exc:
            status = f'{exc.code} {exc.reason}'
        except URLError as exc:
            status = f'ERROR {exc.reason}'
        except Exception as exc:  # pragma: no cover
            status = f'ERROR {exc}'

        return {'label': label, 'url': url, 'status': status}
