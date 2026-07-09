from dataclasses import field
from urllib import request
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator, MinValueValidator, MaxValueValidator


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=15, null=True, blank=True)
    

class Class(models.Model):
    name = models.CharField(max_length=20)
    section = models.CharField(max_length=10, blank=True)

    def __str__(self):
        if self.section:
            return f"{self.name} - Section {self.section}"
        return self.name

    class Meta:
        verbose_name_plural = "Classes"
        ordering = ['name', 'section']


class Subject(models.Model):
    class_name = models.ForeignKey(
        Class, on_delete=models.CASCADE, related_name='subjects'
    )
    name = models.CharField(max_length=100)
    subject_code = models.CharField(max_length=20,unique=True, blank=True)
    full_marks = models.PositiveIntegerField(default=100)
    theory_marks = models.PositiveIntegerField(default=60)
    practical_marks = models.PositiveIntegerField(default=40)
    pass_marks = models.PositiveIntegerField(default=40)
    theory_pass_marks = models.PositiveIntegerField(default=24)
    practical_pass_marks = models.PositiveIntegerField(default=15)

    def save(self, *args, **kwargs):
        if not self.subject_code:
            last = Subject.objects.order_by('-id').first()

            if last:
                number = last.id + 1
            else:
                number = 1

            self.subject_code = f"SUB{number:03d}"

        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.name} ({self.class_name})"

    class Meta:
        ordering = ['name']

def generate_student_id():
    from django.utils import timezone
    year = timezone.now().year
    last = Student.objects.filter(
        student_id__startswith=f'STU-{year}-'
    ).order_by('-id').first()

    number = 1
    if last:
        last_num = int(last.student_id.split('-')[2])
        number = last_num + 1

    return f'STU-{year}-{str(number).zfill(3)}'


class Student(models.Model): 
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    student_id = models.CharField(
        max_length=20,
        unique=True,
        default=generate_student_id,
        editable=False
    )
    roll_number = models.PositiveIntegerField()
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, validators=[MinLengthValidator(10)])
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    date_of_birth = models.DateField(null=True)
    address = models.TextField()
    parent_name = models.CharField(max_length=100, blank=True)
    parent_phone = models.CharField(max_length=15, validators=[MinLengthValidator(10)])
    parent_email = models.EmailField(blank=True)

    class_name = models.ForeignKey(
        'Class',
        on_delete=models.CASCADE,
        related_name='students'
    )
    
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='student_profile'
    )

    def __str__(self):
        return f"{self.student_id} - {self.first_name} {self.last_name} ({self.class_name})"

    class Meta:
        unique_together = ['roll_number', 'class_name']
        ordering = ['class_name', 'roll_number']


class Marks(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='marks'
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE
    )

    theory_obtained = models.FloatField(
        validators=[MinValueValidator(0.0)]
    )

    practical_obtained = models.FloatField(
        validators=[MinValueValidator(0.0)]
    )

    marks_obtained = models.FloatField(
        default=0,
        validators=[MinValueValidator(0.0)]
    )

    percentage = models.FloatField(default=0)
    grade = models.CharField(max_length=5, blank=True)
    is_pass = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.marks_obtained = self.theory_obtained + self.practical_obtained

        self.percentage = round(
            (self.marks_obtained / self.subject.full_marks) * 100, 2
        )

        self.is_pass = (
            self.theory_obtained >= self.subject.theory_pass_marks and
            self.practical_obtained >= self.subject.practical_pass_marks
        )

        p = self.percentage

        if p >= 90:
            self.grade = 'A+'
        elif p >= 80:
            self.grade = 'A'
        elif p >= 70:
            self.grade = 'B+'
        elif p >= 60:
            self.grade = 'B'
        elif p >= 50:
            self.grade = 'C+'
        elif p >= 40:
            self.grade = 'C'
        elif p >= 35:
            self.grade = 'D'
        else:
            self.grade = 'NG'

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} - {self.subject.name}"

    class Meta:
        unique_together = ['student', 'subject']
        
class Result(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    marks_obtained = models.FloatField()
    full_marks = models.FloatField()
    pass_marks = models.FloatField()
    class_name = models.CharField(max_length=50)  
    section = models.CharField(max_length=10)     
    roll_no = models.IntegerField()
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        return f"{self.student.username} - {self.subject}"
    
class Teacher(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
     return self.user.username
    
    
class TeacherAssignment(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='assignments')
    class_assigned = models.ForeignKey(Class, on_delete=models.CASCADE)
    subject_name = models.ForeignKey(Subject, on_delete=models.CASCADE)
    class Meta:
        unique_together = ('teacher', 'class_assigned', 'subject_name')
    def __str__(self):
        return str(self.teacher)