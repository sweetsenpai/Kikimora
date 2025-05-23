import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.authentication import JWTAuthentication

from shop.models import CustomUser
from shop.MongoIntegration.Order import Order
from shop_api.serializers.auth.user import UserDataSerializer
from shop_api.services.authentication import CookieJWTAuthentication

logger = logging.getLogger("shop")


class UserDataView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = UserDataSerializer

    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.is_staff:
            user_id = user.user_id
        else:
            user_id = kwargs.get("user_id", user.user_id)

        try:
            user_data = CustomUser.objects.get(user_id=user_id)
            serializer = self.serializer_class(user_data, many=False)
        except CustomUser.DoesNotExist:
            return Response({"error": "Пользователь не найден."}, status=404)
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    def patch(self, request, **kwargs):
        user = request.user
        user_id = kwargs.get("user_id", user.user_id)
        new_password = request.data.get("new_password")
        old_password = request.data.get("old_password")
        if not user.is_staff and user.user_id != user_id:
            return Response(
                {"error": "У вас нет прав для изменения этих данных."}, status=403
            )

        try:
            user_data = CustomUser.objects.get(user_id=user_id)
        except CustomUser.DoesNotExist:
            return Response({"error": "Пользователь не найден."}, status=404)

        if new_password:
            if not user.is_staff and not old_password:
                return Response({"error": "Требуется старый пароль."}, status=400)
            if not user.is_staff and not user.check_password(old_password):
                return Response({"error": "Неверный старый пароль."}, status=400)
            user.set_password(new_password)

        serializer = self.serializer_class(user_data, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            if new_password:
                user.save()
            return Response(status=status.HTTP_200_OK, data=serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UsersOrder(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        try:
            user = request.user
            if not user:
                return Response(
                    {"error: Пользователь ненайден"}, status=status.HTTP_404_NOT_FOUND
                )
            orders = Order().get_users_orders(user.user_id)
            return Response(status=status.HTTP_200_OK, data={"orders": orders})
        except Exception as e:
            logger.error(
                f"Вовремя выдачи истории заказов пользователя произошла непредвиденная ошибка.\nERROR:{e}"
            )
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)
