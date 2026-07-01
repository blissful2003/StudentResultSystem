from django.contrib import admin
from .models import Student, Class, Subject, Marks, Teacher

admin.site.register(Student)
admin.site.register(Class)
admin.site.register(Subject)
admin.site.register(Marks)
admin.site.register(Teacher)

