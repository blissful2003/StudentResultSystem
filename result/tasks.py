from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def send_student_credentials(email,first_name, username, password):
    login_url = "http://127.0.0.1:8000/student/login/"
    send_mail(
        subject="Your Student Account Credentials",
        message=f"""
Hello {first_name},

Your student account has been created.

Username: {username}
Password: {password}
Login here:
{login_url}

Please login using these credentials.

Thank you.
""",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
         fail_silently=False,
    )

@shared_task
def test_task():
    return "Celery working"




