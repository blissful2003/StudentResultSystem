from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def send_student_credentials(email, username, password):

    send_mail(
        subject="Your Student Account Credentials",
        message=f"""
Hello,

Your student account has been created.

Username: {username}
Password: {password}

Please login using these credentials.

Thank you.
""",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
    )