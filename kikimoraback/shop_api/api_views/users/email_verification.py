from rest_framework.views import APIView

from shop.models import CustomUser
from shop.services.email_verification import verify_email_token


class VerifyEmailView(APIView):
    def get(self, request, token):
        user_id = verify_email_token(token)
        if user_id:
            try:
                user = CustomUser.objects.get(user_id=user_id)
                if not user.is_email_verified:
                    user.is_email_verified = True
                    user.save()
                    # TODO путь к template
                    return render(
                        request,
                        "emails/email_confirmed.html",
                        {"website_url": os.getenv("WEBSITE_URL")},
                    )
                else:
                    return render(
                        request,
                        "emails/email_confirmed.html",
                        {
                            "website_url": os.getenv("WEBSITE_URL"),
                            "message": "Email уже был подтвержден ранее.",
                        },
                    )
            except CustomUser.DoesNotExist:
                pass
            return render(
                request,
                "emails/email_confirmed.html",
                {
                    "website_url": os.getenv("WEBSITE_URL"),
                    "message": "Недействительная ссылка для подтверждения.",
                },
            )
