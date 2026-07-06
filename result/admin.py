from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Class, Subject, Student, Marks, Teacher, TeacherAssignment


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'role', 'phone', 'is_staff', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Extra Info', {'fields': ('role', 'phone')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Extra Info', {'fields': ('role', 'phone')}),
    )


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Class)
admin.site.register(Subject)
admin.site.register(Student)
admin.site.register(Marks)
admin.site.register(Teacher)
admin.site.register(TeacherAssignment)