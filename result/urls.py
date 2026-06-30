

from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_login, name='login'),
    path('logout/', views.admin_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.add_student, name='add_student'),
    path('subjects/add/', views.add_subject, name='add_subject'),
    path('marks/add/', views.add_marks, name='add_marks'),
    path('result/<int:pk>/', views.student_result, name='student_result'),
    path('marks/edit/<int:pk>/', views.edit_marks, name='edit_marks'),
    path('students/edit/<int:pk>/', views.edit_student, name='edit_student'),
    path('students/delete/<int:pk>/', views.delete_student, name='delete_student'),
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/edit/<int:pk>/', views.edit_subject, name='edit_subject'),
    path('subjects/delete/<int:pk>/', views.delete_subject, name='delete_subject'),
    path('classes/add/', views.add_class, name='add_class'),
    path('profile/', views.profile, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('student/login/', views.student_login, name='student_login'),
    path('student/logout/', views.student_logout, name='student_logout'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/result/', views.student_own_result, name='student_own_result'),
    path('student/result/all/', views.student_result_view, name='student_all_results'),
]
