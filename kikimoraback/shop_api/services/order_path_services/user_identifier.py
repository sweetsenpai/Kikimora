import uuid
from django.contrib.auth.models import AnonymousUser
from rest_framework.response import Response
from rest_framework import status
from shop.models import CustomUser

class UserIdentifierService:
    def __init__(self, request):
        self.request = request
        self.user = request.user

    def get_or_create_user_id(self):
        if not isinstance(self.user, AnonymousUser):
            try:
                user_id = CustomUser.objects.get(user_id=self.user.user_id).user_id
                return user_id, None
            except CustomUser.DoesNotExist:
                return None, Response(
                    {"error": "Пользователь не найден."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            user_id = self.request.COOKIES.get("user_id")
            if not user_id:
                user_id = str(uuid.uuid4())

                return user_id, {
                    "key": "user_id",
                    "value": user_id,
                    "options": {
                        "max_age": 60 * 60 * 24 * 30,
                        "httponly": True,
                        "secure": True,
                    }
                }
            return user_id, None
