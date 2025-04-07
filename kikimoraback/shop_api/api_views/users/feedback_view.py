from rest_framework.response import Response
from rest_framework.views import APIView

from shop.tasks import feedback_email


class FeedBackApi(APIView):
    def post(self, request):
        try:
            feedback_data = {
                "name": request.data.get("name"),
                "phone": request.data.get("phone"),
                "email": request.data.get("email"),
                "question": request.data.get("question"),
            }
            feedback_email.delay(feedback_data)  # Вызываем задачу через Celery
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(
                f"Во время отправки обратной связи произошла непредвиденная ошибка.\nERROR: {e}"
            )
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
