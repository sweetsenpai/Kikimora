import smtplib
import ssl

smtp_server = "smtp.yandex.ru"
port = 465  # For starttls
sender_email = "chcolatemilk00@yandex.ru"
password = 'mmppvuxofkxbmdib'
receiver_email = "chcolatemilk00@gmail.com"  # Enter receiver address

message = """\
Subject: Hi there

This message is sent from Python."""

context = ssl.create_default_context()
with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
    server.login(sender_email, password)
    print(server)
    x = server.sendmail(sender_email, receiver_email, message)
    print(x)