from django.core.mail import send_mail
from result.models import Result
def send_result_email(class_id):
    results = Result.object.filter(student_class_id=class_id, is_published=True)
    for result in results:
        status = "Pass" if result.is_pass else "FAIL"
        send_mail(
            subject=f"Your Result has been Published - {result.student.name}",
            message=f"Dear {result.student.name}, \n\nYour result has been published.\n"
                    f"Total Marks: {result.total_marks}\nStatus: {status}\n\n"
                    f"Login to check details.",
            from_email=None,
            recipient_list=[result.student.email],
            fail_silently=False,
        )