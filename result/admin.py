from django.contrib import admin
from .models import Student, Class, Subject, Marks

admin.site.register(Student)
admin.site.register(Class)
admin.site.register(Subject)
admin.site.register(Marks)
