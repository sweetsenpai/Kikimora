from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from shop_api.serializers.auth.registration import RegistrationSerializer
from shop_api.serializers.auth.user import UserDataSerializer
from shop_api.tasks.emails.user_emails import send_confirmation_email
import logging
logger = logging.getLogger('shop')


# TODO куки на деплое
class RegisterUserView(APIView):
    def post(self, request):
        user = None  # Инициализируем переменную для хранения созданного пользователя
        try:
            serializer = RegistrationSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()  # Создаем пользователя
                refresh = RefreshToken.for_user(user)

                response = JsonResponse({
                    "message": "Пользователь успешно зарегистрирован.",
                    "user": UserDataSerializer(user).data
                }, status=status.HTTP_201_CREATED)

                # Устанавливаем cookies
                response.set_cookie(
                    key="access_token",
                    value=str(refresh.access_token),
                    httponly=True,
                    secure=False,  # В production должно быть True
                    samesite='Lax'
                )
                response.set_cookie(
                    key="refresh_token",
                    value=str(refresh),
                    httponly=True,
                    secure=False,  # В production должно быть True
                    samesite='Lax'
                )

                # Отправляем письмо подтверждения
                try:
                    send_confirmation_email.delay(UserDataSerializer(user).data)
                except Exception as e:
                    logger.error(f"Во время отправки письма для верификации email произошла ошибка.\n"
                                 f"user_data: {user}\n"
                                 f"error: {e}")

                return response
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Удаляем пользователя, если он был создан
            if user:
                try:
                    user.delete()
                    logger.info(f"Пользователь с ID {user.id} удален из-за возникшей ошибки.")
                except Exception as delete_error:
                    logger.error(f"Ошибка при удалении пользователя с ID {user.id}: {delete_error}")

            logger.error("Ошибка во время регистрации нового пользователя."
                         f"request: {request.data}\n"
                         f"error: {e}")
            return Response({"error": "Сервис временно не доступен. Попробуйте перезагрузить страницу."},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)