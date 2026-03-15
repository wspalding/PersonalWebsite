import hashlib

from django.conf import settings
from django.utils import timezone

from .models import Visit


class VisitTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if not getattr(settings, 'VISITOR_TRACKING_ENABLED', True):
            return response

        if request.method != 'GET':
            return response

        if response.status_code >= 500:
            return response

        if self.should_skip(request, response):
            return response

        client_ip = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        fingerprint_source = f"{client_ip}|{user_agent}"

        Visit.objects.create(
            path=request.path,
            visitor_fingerprint=hashlib.sha256(fingerprint_source.encode('utf-8')).hexdigest(),
            ip_hash=hashlib.sha256(client_ip.encode('utf-8')).hexdigest(),
            user_agent_hash=hashlib.sha256(user_agent.encode('utf-8')).hexdigest() if user_agent else '',
            referrer=request.META.get('HTTP_REFERER', '')[:1024],
            visit_day=timezone.localdate(),
        )

        return response

    def should_skip(self, request, response):
        for prefix in getattr(settings, 'VISITOR_TRACKING_EXCLUDED_PATH_PREFIXES', ()):
            if request.path.startswith(prefix):
                return True

        if 'text/html' not in response.get('Content-Type', ''):
            return True

        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        return any(
            fragment in user_agent
            for fragment in getattr(settings, 'VISITOR_TRACKING_BOT_SUBSTRINGS', ())
        )

    @staticmethod
    def get_client_ip(request):
        forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
