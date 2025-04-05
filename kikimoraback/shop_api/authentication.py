from django.conf import settings

from rest_framework.exceptions import AuthenticationFailed

from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # Извлекаем access_token из cookies
        access_token = request.COOKIES.get(
            settings.JWT_COOKIE_SETTINGS["ACCESS_TOKEN_COOKIE"]
        )
        if not access_token:
            return None

        # Устанавливаем токен в заголовок Authorization для обработки JWTAuthentication
        request.META["HTTP_AUTHORIZATION"] = f"Bearer {access_token}"

        try:
            return super().authenticate(request)
        except AuthenticationFailed:
            # Если токен недействителен, выбрасываем ошибку
            raise AuthenticationFailed("Недействительный токен.")
