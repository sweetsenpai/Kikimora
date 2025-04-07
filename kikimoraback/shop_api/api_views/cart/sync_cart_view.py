from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.authentication import JWTAuthentication

from shop.models import CustomUser
from shop.MongoIntegration.Cart import Cart


class SyncCart(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        front_data = request.data.get("cart")
        user = request.user
        try:
            user_data = CustomUser.objects.get(user_id=user.user_id)
        except CustomUser.DoesNotExist:
            return Response({"error": "Пользователь не найден."}, status=404)
        cart = Cart()

        return Response(
            data=cart.sync_cart_data(
                user_id=user_data.user_id, front_cart_data=front_data
            ),
            status=status.HTTP_200_OK,
        )
