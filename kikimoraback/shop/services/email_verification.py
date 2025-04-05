from django.conf import settings

from itsdangerous import URLSafeTimedSerializer


def generate_email_token(user_id):
    serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
    token = serializer.dumps(user_id, salt="email-confirmation")
    return token


def verify_email_token(token, max_age=86400 * 7):
    serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
    try:
        user_id = serializer.loads(token, salt="email-confirmation", max_age=max_age)
        return user_id
    except Exception as e:
        logger.critical(
            "Вовремя создания токена верификации email произошла не предвиденная ошибка.\n"
            f"ERROR: {e}"
        )
        return None
