import logging

from django.http import JsonResponse

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken

from shop_api.serializers.auth.registration import RegistrationSerializer
from shop_api.serializers.auth.user import UserDataSerializer
from shop_api.tasks.emails.user_emails import send_confirmation_email

logger = logging.getLogger("shop")


# TODO куки на деплое
class RegisterUserView(APIView):
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            response = JsonResponse(
                {
                    "message": "Пользователь успешно зарегистрирован.",
                    "tokens": {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    },
                    "user": UserDataSerializer(user).data,
                },
                status=status.HTTP_201_CREATED,
            )

            response.set_cookie(
                "access_token",
                str(refresh.access_token),
                httponly=True,
                secure=True,
                samesite="Strict",
            )
            response.set_cookie(
                "refresh_token",
                str(refresh),
                httponly=True,
                secure=True,
                samesite="Strict",
            )

            send_confirmation_email(user)

            return response
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
