from django.conf import settings
from django.core.mail import send_mail


def new_admin_mail(password, email):
    send_mail('Готов вкалывать?',
                          f'Привет новый ра..сотрудник!\n'
                          f'Для входа в систему тебе нужен логин и пароль.\n'
                          f'Пароль я дам:  {password}  , логин я не дам... \n'
                          f'Логин это твоя почта она у тебя и так есть.\n'
                          f'Только прошу, не давай пароль никому кроме себя, а то всем придется не сладко, особенно тебе!',
                          'settings.EMAIL_HOST_USER',
                          [email],
                          fail_silently=False)