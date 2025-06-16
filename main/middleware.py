from django.http import HttpResponseForbidden
from .models import BlockedIP
from django.utils import timezone

class BlockIPMiddleware:
    """
    Middleware для блокировки IP-адресов.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Получаем IP-адрес клиента
        ip_address = self.get_client_ip(request)

        # Проверяем, заблокирован ли IP-адрес
        if BlockedIP.objects.filter(ip_address=ip_address, blocked_until__gte=timezone.now()).exists():
            return HttpResponseForbidden("Ваш IP-адрес заблокирован.")

        # Продолжаем обработку запроса
        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        """
        Получает IP-адрес клиента из заголовков запроса.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
