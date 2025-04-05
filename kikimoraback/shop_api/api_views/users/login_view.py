from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.http import JsonResponse

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken

# TODO изменить secure=True,  samesite='None' для прода


class Login(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = authenticate(request, email=email, password=password)

        if user:
            refresh = RefreshToken.for_user(user)
            update_last_login(None, user)

            response = JsonResponse(
                {
                    "message": "Успешный вход.",
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                status=status.HTTP_200_OK,
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
            return response
        else:
            return Response(
                {"error": "Неверный логин или пароль."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
