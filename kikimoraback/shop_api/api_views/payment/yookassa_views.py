import logging

from django.views.decorators.csrf import csrf_exempt

from rest_framework.response import Response
from rest_framework.views import APIView

from yookassa.domain.common import SecurityHelper
from yookassa.domain.notification import WebhookNotificationEventType, WebhookNotificationFactory

from shop_api.tasks.payment_tasks.payment_canceled_tasks import process_payment_canceled
from shop_api.tasks.payment_tasks.payment_succeeded_tasks import process_payment_succeeded

logger = logging.getLogger("shop")
logger.setLevel(logging.DEBUG)


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


@csrf_exempt
def yookassa_webhook(request):
    ip = get_client_ip(request)
    if not SecurityHelper().is_ip_trusted(ip):
        logger.warning("Попытка получить доступ к API оплаты из незарегистрированного источника.")
        return HttpResponse(status=400)

    event_json = json.loads(request.body)
    try:
        notification_object = WebhookNotificationFactory().create(event_json)
        response_object = notification_object.object

        if notification_object.event == WebhookNotificationEventType.PAYMENT_SUCCEEDED:
            payment_id = response_object.id
            process_payment_succeeded.delay(payment_id)
        elif notification_object.event == WebhookNotificationEventType.PAYMENT_CANCELED:
            payment_id = response_object.id
            process_payment_canceled.delay(payment_id)

        return Response(status=status.HTTP_200_OK)  # Быстрый ответ YooKassa

    except Exception as e:
        logger.error(f"Ошибка при обработке вебхука YooKassa: {str(e)}, данные: {event_json}")
        return Response(status=status.HTTP_400_BAD_REQUEST)


class TestWebhook(APIView):
    def post(self, request):
        payment_id = "2f3c3b0a-000f-5000-9000-1c5f664e2afd"
        try:
            process_payment_succeeded(payment_id)
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            logger.debug(f"Ошибка при обработке вебхука YooKassa: {str(e)}")
            return Response(status=status.HTTP_400_BAD_REQUEST)
