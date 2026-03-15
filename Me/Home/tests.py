from datetime import timedelta
from unittest.mock import patch

from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from .models import Visit


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    REPORT_EMAIL_TO=['owner@example.com'],
    REPORT_EMAIL_FROM='website@example.com',
    SITE_PUBLIC_URL='https://williamspalding.com/',
    VISIT_RETENTION_DAYS=180,
)
class VisitTrackingTests(TestCase):
    def test_page_request_creates_visit(self):
        response = self.client.get('/', HTTP_USER_AGENT='Mozilla/5.0')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Visit.objects.count(), 1)
        visit = Visit.objects.get()
        self.assertEqual(visit.path, '/')

    def test_bot_request_is_ignored(self):
        self.client.get('/', HTTP_USER_AGENT='curl/8.0.1')

        self.assertEqual(Visit.objects.count(), 0)

    def test_admin_path_is_ignored(self):
        self.client.get('/admin/login/', HTTP_USER_AGENT='Mozilla/5.0')

        self.assertEqual(Visit.objects.count(), 0)

    @patch('Home.management.commands.send_website_report.Command.handle_service_statuses')
    @patch('Home.management.commands.send_website_report.Command.check_url')
    def test_report_command_sends_email(self, mock_check_url, mock_service_statuses):
        now = timezone.now()
        Visit.objects.create(
            path='/',
            visitor_fingerprint='visitor-a',
            ip_hash='ip-a',
            user_agent_hash='ua-a',
            referrer='',
            created_at=now,
            visit_day=now.date(),
        )
        Visit.objects.create(
            path='/projects/',
            visitor_fingerprint='visitor-b',
            ip_hash='ip-b',
            user_agent_hash='ua-b',
            referrer='',
            created_at=now,
            visit_day=now.date(),
        )
        Visit.objects.create(
            path='/',
            visitor_fingerprint='visitor-a',
            ip_hash='ip-a',
            user_agent_hash='ua-a',
            referrer='',
            created_at=now - timedelta(hours=1),
            visit_day=now.date(),
        )

        mock_service_statuses.return_value = {
            'nginx': 'active',
            'daphne': 'active',
            'cloudflared': 'active',
        }
        mock_check_url.side_effect = [
            {'label': 'Public site', 'url': 'https://williamspalding.com/', 'status': '200 OK'},
            {'label': 'Local origin', 'url': 'http://127.0.0.1/', 'status': '200 OK'},
        ]

        call_command('send_website_report')

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn('Page views (last 24 hours): 3', email.body)
        self.assertIn('Unique visitors (last 24 hours): 2', email.body)
        self.assertIn('Old visit records pruned: 0 (retention: 180 days)', email.body)

    @patch('Home.management.commands.send_website_report.Command.handle_service_statuses')
    @patch('Home.management.commands.send_website_report.Command.check_url')
    def test_report_command_prunes_old_visits(self, mock_check_url, mock_service_statuses):
        now = timezone.now()
        old_timestamp = now - timedelta(days=181)

        old_visit = Visit.objects.create(
            path='/old/',
            visitor_fingerprint='old-visitor',
            ip_hash='old-ip',
            user_agent_hash='old-ua',
            referrer='',
            visit_day=old_timestamp.date(),
        )
        Visit.objects.filter(pk=old_visit.pk).update(created_at=old_timestamp)

        Visit.objects.create(
            path='/current/',
            visitor_fingerprint='current-visitor',
            ip_hash='current-ip',
            user_agent_hash='current-ua',
            referrer='',
            visit_day=now.date(),
        )

        mock_service_statuses.return_value = {
            'nginx': 'active',
            'daphne': 'active',
            'cloudflared': 'active',
        }
        mock_check_url.side_effect = [
            {'label': 'Public site', 'url': 'https://williamspalding.com/', 'status': '200 OK'},
            {'label': 'Local origin', 'url': 'http://127.0.0.1/', 'status': '200 OK'},
        ]

        call_command('send_website_report')

        self.assertFalse(Visit.objects.filter(path='/old/').exists())
        self.assertTrue(Visit.objects.filter(path='/current/').exists())
        self.assertIn('Old visit records pruned: 1 (retention: 180 days)', mail.outbox[0].body)
