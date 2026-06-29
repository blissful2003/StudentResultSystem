

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Student

@receiver(post_save, sender=Student)
def create_user_for_student(sender, instance, created, **kwargs):
    if created and not instance.user:
    
        username = instance.student_id
        password = instance.date_of_birth.strftime('%Y%m%d')

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=instance.first_name,
            last_name=instance.last_name,
            email=instance.email,
        )

        
        instance.user = user
        instance.save()