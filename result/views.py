from ast import Return
import csv
from django.utils import timezone
import email
from itertools import count
from pickle import MARK
import secrets
import string
from urllib import request
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from result.decorators import teacher_required
from .models import Resultpublished, Teacher, TeacherAssignment, Subject, Class
from .models import Result, Student, Subject, Marks, Class, Teacher, TeacherAssignment, generate_student_id
from .forms import StudentForm, SubjectForm, MarksForm, ClassForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import get_user_model
from .tasks import send_student_credentials
from django.core.mail import send_mail

User = get_user_model()

def admin_login(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
         return redirect('result:dashboard')
        else:
            return redirect('result:teacher_dashboard')
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user is not None:
            auth_login(request, user)
            if user.is_superuser:
             return redirect('result:dashboard')
            else:
                return redirect('result:teacher_dashboard')
        messages.error(request, 'Username and password incorrect!')
    return render(request, 'result/login.html')


def admin_logout(request):
    auth_logout(request)
    return redirect('result:admin_login')


@login_required(login_url='result:admin_login')
def dashboard(request):
    if not request.user.is_superuser:
        messages.error(request, "Access Denied!")
        return redirect('result:teacher_dashboard')

    return render(request, 'result/dashboard.html', {
        'total_students': Student.objects.count(),
        'total_subjects': Subject.objects.count(),
        'pass_count': Marks.objects.filter(is_pass=True).count(),
        'fail_count': Marks.objects.filter(is_pass=False).count(),
    })


@login_required(login_url='result:admin_login')
def student_list(request):
    query = request.GET.get('roll', '')
    selected_class = request.GET.get('class_id', '')
    classes = Class.objects.all()

    if query or selected_class:
        students = Student.objects.all()
        if query:
            students = students.filter(roll_number__icontains=query)
        if selected_class:
            students = students.filter(class_name_id=selected_class)
        grouped = None
    else:
        students = None
        grouped = []
        for cls in classes:
            cls_students = Student.objects.filter(class_name=cls)
            if cls_students.exists():
                grouped.append({
                    'class': cls,
                    'students': cls_students
                })
    return render(request, 'result/student_list.html', {
        'students': students,
        'grouped': grouped,
        'query': query,
        'classes': classes,
        'selected_class': selected_class,
    })
@login_required(login_url='result:admin_login')
def add_student(request):

    if request.method == 'POST':

        form = StudentForm(request.POST)

        if form.is_valid():

            student = form.save(commit=False)

            student.student_id = generate_student_id()

            username = student.student_id
            password = student.date_of_birth.strftime('%Y%m%d')

            if User.objects.filter(username=username).exists():

                messages.error(
                    request,
                    f'Username {username} already exists!'
                )

                return render(request,'result/add_student.html',{'form': form,'classes': Class.objects.all()})

            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=student.first_name,
                last_name=student.last_name,
                email=student.email,
                role='student',
            )

            student.user = user
            student.save()
            send_student_credentials.delay(
                student.email,
                student.first_name,
                username,
                password
            )
            messages.success(request, f'Student added! Username: {username} Password: {password}')
            return redirect('result:student_list')
        else:
            messages.error(request, form.errors)
    else:
        form = StudentForm()
    return render(request,'result/add_student.html',{'form': form,'classes': Class.objects.all()})


@login_required(login_url='result:admin_login')
def edit_student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            updated_student = form.save(commit=False)
            if student.user:
                student.user.first_name = updated_student.first_name
                student.user.last_name = updated_student.last_name
                student.user.email = updated_student.email
                student.user.save()
            updated_student.save()
            messages.success(request, 'Student updated!')
            return redirect('result:student_list')
    else:
        form = StudentForm(instance=student)
    return render(request, 'result/add_student.html', {'form': form, 'edit': True})


@login_required(login_url='result:admin_login')
def delete_student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        if student.user:
            student.user.delete()
        student.delete()
        messages.success(request, 'Student deleted!')
        return redirect('result:student_list')
    return render(request, 'result/confirm_delete.html', {'student': student})

@login_required(login_url='result:admin_login')
def upload_students(request):
    classes = Class.objects.all()

    if request.method == "POST":

        class_id = request.POST.get("class_id")
        csv_file = request.FILES.get("csv_file")

        if not csv_file:
            messages.error(request, "Please select CSV file")
            return redirect('result:upload_students')

        selected_class = Class.objects.get(id=class_id)

        decoded_file = csv_file.read().decode("utf-8-sig").splitlines()
        reader = csv.DictReader(decoded_file)

        count = 0

        for row in reader:

            if Student.objects.filter(
                class_name=selected_class,
                roll_number=row['roll_number']
            ).exists():
                continue

            if Student.objects.filter(phone=row['phone']).exists():
                continue

            student_id = generate_student_id()
            username = student_id
            password = row['date_of_birth'].replace("-", "")

            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=row['first_name'],
                last_name=row['last_name'],
                email=row['email'],
                role='student'
            )


            student = Student.objects.create(
                user=user,
                student_id=student_id,
                roll_number=row['roll_number'],
                first_name=row['first_name'],
                last_name=row['last_name'],
                email=row['email'],
                phone=row['phone'],
                gender=row['gender'],
                date_of_birth=row['date_of_birth'],
                address=row['address'],
                class_name=selected_class,
                parent_name=row['parent_name'],
                parent_phone=row['parent_phone'],
                parent_email=row['parent_email']
            )
  
            send_student_credentials.delay(
                student.email,
                student.first_name,
                username,
                password
            )

            count += 1

            print(student.first_name)
            print(student.student_id)

        print("Total uploaded:", count)

        messages.success(request,f"{count} Students uploaded successfully!")
        return redirect('result:dashboard')

    return render(request,"result/upload_students.html",{"classes": classes})

@login_required(login_url='result:admin_login')
def add_subject(request):
    form = SubjectForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Subject added successfully!')
        return redirect('result:dashboard')
    else:
         print(form.errors)
    return render(request, 'result/add_subject.html', {'form': form})


@login_required(login_url='result:admin_login')
def admin_add_marks(request):
    form = MarksForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Marks added successfully!')
        return redirect('result:student_list')
    return render(request, 'result/add_marks.html', {'form': form})


@login_required(login_url='result:admin_login')
def student_result(request, pk):
    student = get_object_or_404(Student, pk=pk)
    marks_list = Marks.objects.filter(student=student)
    total_obtained = sum(m.marks_obtained for m in marks_list)
    total_full = sum(m.subject.full_marks for m in marks_list)
    overall_pct = round((total_obtained / total_full * 100) if total_full else 0, 2)
    return render(request, 'result/student_result.html', {
        'student': student,
        'marks_list': marks_list,
        'total_obtained': total_obtained,
        'total_full': total_full,
        'overall_pct': overall_pct,
    })


@login_required(login_url='result:admin_login')
def edit_marks(request, pk):
    mark = get_object_or_404(Marks, pk=pk)
    form = MarksForm(request.POST or None, instance=mark)
    if form.is_valid():
        form.save()
        messages.success(request, 'Marks updated successfully!')
        return redirect('result:student_result', pk=mark.student.pk)
    return render(request, 'result/add_marks.html', {'form': form, 'edit': True})


@login_required(login_url='result:admin_login')
def subject_list(request):
    subjects = Subject.objects.all()
    return render(request, 'result/subject_list.html', {'subjects': subjects})


@login_required(login_url='result:admin_login')
def edit_subject(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    form = SubjectForm(request.POST or None, instance=subject)
    if form.is_valid():
        form.save()
        messages.success(request, 'Subject updated successfully!')
        return redirect('result:subject_list')
    return render(request, 'result/add_subject.html', {'form': form, 'edit': True})


@login_required(login_url='result:admin_login')
def delete_subject(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        subject.delete()
        messages.success(request, 'Subject deleted successfully!')
        return redirect('result:subject_list')
    return render(request, 'result/confirm_delete_subject.html', {'subject': subject})


@login_required(login_url='result:admin_login')
def add_class(request):
    next_page = request.GET.get('next') or request.POST.get('next') or 'add_subject'

    form = ClassForm(request.POST or None)

    if form.is_valid():
        form.save()
        messages.success(request, 'Class added successfully!')
        return redirect('result:' + next_page)

    return render(request, 'result/add_class.html', {
        'form': form,
        'next': next_page
    })

@login_required(login_url='result:admin_login')
def profile(request):
    return render(request, 'result/profile.html', {'user': request.user})


@login_required(login_url='result:admin_login')
def change_password(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, 'Password changed successfully!')
        return redirect('result:profile')
    return render(request, 'result/change_password.html', {'form': form})


def student_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )
        if user and hasattr(user, 'student_profile'):
            auth_login(request, user)
            student = user.student_profile
            if student.must_change_password:
             return redirect("result:password_setup")
            return redirect('result:student_dashboard')
        else:
            messages.error(request, 'Invalid username or password!')
    return render(request, 'student/login.html')


def student_logout(request):
    auth_logout(request)
    return redirect('result:student_login')


@login_required(login_url='result:student_login')
def student_dashboard(request):
    try:
        student = request.user.student_profile
    except:
        return redirect('result:student_login')

    my_marks = Marks.objects.filter(student=student)

    total_obtained = sum(m.marks_obtained for m in my_marks)
    total_full = sum(m.subject.full_marks for m in my_marks)

    overall_pct = round((total_obtained / total_full * 100) if total_full else 0, 2)

    
    overall_pass = all(mark.is_pass for mark in my_marks)

    
    if overall_pct >= 90:
        overall_grade = "A+"
    elif overall_pct >= 80:
        overall_grade = "A"
    elif overall_pct >= 70:
        overall_grade = "B+"
    elif overall_pct >= 60:
        overall_grade = "B"
    elif overall_pct >= 50:
        overall_grade = "C+"
    elif overall_pct >= 40:
        overall_grade = "C"
    else:
        overall_grade = "NG"

    return render(request, 'student/dashboard.html', {
        'student': student,
        'marks_list': my_marks,
        'total_obtained': total_obtained,
        'total_full': total_full,
        'overall_pct': overall_pct,
        'overall_grade': overall_grade,
        'is_overall_pass': overall_pass,
    })

@login_required(login_url='result:student_login')
def student_profile(request):
    try:
        student = request.user.student_profile
    except:
        return redirect('result:student_login')

    context = {
        'student': student
    }

    return render(request, 'student/student_profile.html', context)

@login_required(login_url='result:student_login')
def student_own_result(request):
    try:
        student = request.user.student_profile
    except:
        return redirect('result:student_login')
    marks_list = Marks.objects.filter(student=student)
    total_obtained = sum(m.marks_obtained for m in marks_list)
    total_full = sum(m.subject.full_marks for m in marks_list)
    overall_pct = round((total_obtained / total_full * 100) if total_full else 0, 2)
    return render(request, 'student/result.html', {
        'student': student,
        'marks_list': marks_list,
        'total_obtained': total_obtained,
        'total_full': total_full,
        'overall_pct': overall_pct,
    })

@login_required(login_url='result:student_login')
def student_result_view(request):
    student = get_object_or_404(Student, user=request.user)

    published = Resultpublished.objects.filter(
        class_name=student.class_name,
        is_published=True
    ).exists()

    if not published:
        return render(request, 'student/result.html', {
            'student': student,
            'not_published': True,
        })

    marks_list = Marks.objects.filter(student=student)

    if not marks_list.exists():
        return render(request, 'student/result.html', {
            'student': student,
            'not_published': True,
        })

    overall_pass = all(m.is_pass for m in marks_list)
    total_obtained = sum(m.marks_obtained for m in marks_list)
    total_full = sum(m.subject.full_marks for m in marks_list)

    context = {
        'student': student,
        'marks_list': marks_list,
        'overall_status': 'Pass' if overall_pass else 'Fail',
        'total_obtained': total_obtained,
        'total_full': total_full,
    }

    return render(request, 'student/result.html', context)
def teacher_profile(request):
    teacher = Teacher.objects.get(user=request.user)
    assignments = TeacherAssignment.objects.filter(
        teacher=teacher
    ).select_related('class_assigned', 'subject_name')

    context = {
        'teacher': teacher,
        'assignments': assignments,
    }

    return render(request, 'result/teacher/profile.html', context)

def teacher_login(request):
    if request.method =='POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user and hasattr(user, 'teacher'):
            auth_login(request, user)
            return redirect('result:teacher_dashboard')
        else:
            messages.error(request, 'Invalid username and password!')
    return render(request, 'teacher/login.html')


def teacher_logout(request):
    auth_logout(request)
    return redirect('result:teacher_login')


@login_required(login_url='result:teacher_login')
def teacher_dashboard(request):
    teacher = request.user.teacher

    assignments = TeacherAssignment.objects.filter(
        teacher=teacher
    ).select_related(
        'class_assigned',
        'subject_name'
    )

    dashboard_data = []

    for assignment in assignments:

        students = Student.objects.filter(class_name=assignment.class_assigned).order_by('roll_number')
        student_data = []
        for student in students:
            mark = Marks.objects.filter(
                student=student,
                subject=assignment.subject_name
            ).first()
            student_data.append({'student': student,'mark': mark,'status': (
                    'Pass' if mark and mark.is_pass
                    else 'Fail' if mark
                    else 'Not Added'
                )
            })

        dashboard_data.append({'assignment': assignment,'students': student_data,})
    return render(request,'teacher/dashboard.html',{'dashboard_data': dashboard_data})

@teacher_required
def add_mark(request, student_id, subject_id, class_id):
    print("View reached")

    teacher = request.user.teacher

    assignment = get_object_or_404(
        TeacherAssignment,
        teacher=teacher,
        class_assigned_id=class_id,
        subject_name_id=subject_id
    )

    student = get_object_or_404(Student, id=student_id, class_name_id=class_id)
    subject = assignment.subject_name

    mark_instance = Marks.objects.filter(student=student, subject=subject).first()

    if request.method == 'POST':
        form = MarksForm(
            request.POST,
            instance=mark_instance,
            subject=subject          
        )

        if form.is_valid():
            mark = form.save(commit=False)
            mark.student = student
            mark.subject = subject
            mark.save()

            messages.success(request, "Marks saved successfully.")
            return redirect('result:teacher_dashboard')
        else:
            print(form.errors)

    else:
        form = MarksForm(instance=mark_instance, subject=subject)   

    return render(request, 'teacher/add_mark.html', {'form': form, 'student': student, 'subject': subject})
    

@teacher_required
def view_mark(request, mark_id):
    teacher = request.user.teacher
    mark = get_object_or_404(Marks, id=mark_id)
    is_authorized = TeacherAssignment.objects.filter(teacher=teacher, subject_name=mark.subject).exists()
    if not is_authorized:
        messages.error(request, "Unauthorized.")
        return redirect('result:teacher_dashboard')
    return render(request, 'teacher/view_mark.html', {'mark': mark})


@teacher_required
def edit_mark(request, mark_id):
    teacher = request.user.teacher
    mark = get_object_or_404(Marks, id=mark_id)

    is_authorized = TeacherAssignment.objects.filter(teacher=teacher, subject_name=mark.subject).exists()
    if not is_authorized:
        messages.error(request, "Unauthorized.")
        return redirect('result:teacher_dashboard')

    if request.method == 'POST':
        form = MarksForm(request.POST, instance=mark)
        if form.is_valid():
            form.save()
            messages.success(request, "Marks updated successfully.")
            return redirect('result:teacher_dashboard')
    else:
        form = MarksForm(instance=mark)

    return render(request, 'teacher/edit_mark.html', {'form': form, 'student': mark.student, 'subject': mark.subject})
@teacher_required
def delete_mark(request, mark_id):
    teacher = request.user.teacher
    mark = get_object_or_404(Marks, id=mark_id)

    is_authorized = TeacherAssignment.objects.filter(teacher=teacher, subject_name=mark.subject).exists()
    if not is_authorized:
        messages.error(request, "Unauthorized.")
        return redirect('result:teacher_dashboard')

    mark.delete()

    messages.success(request, "Marks deleted successfully.")
    return redirect('result:teacher_dashboard')

def generate_password(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

@login_required(login_url='result:admin_login')
def teacher_list(request):
    if not request.user.is_staff:
        return redirect('result:dashboard')
    teachers = Teacher.objects.select_related('user').prefetch_related('assignments__subject_name','assignments__class_assigned')
    return render(request, 'result/teacher_list.html', {'teachers': teachers})

@login_required(login_url='result:admin_login')
def add_teacher(request):
    if not request.user.is_staff:
        return redirect('result:dashboard')

    subjects = Subject.objects.all()
    classes = Class.objects.all()

    if request.method == 'POST':

        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email', '')

        class_ids = request.POST.getlist('class_ids')
        subject_ids = request.POST.getlist('subject_ids')


        username = f"{first_name.lower()}{secrets.randbelow(900)+100}"
        password = generate_password()

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role='teacher',
        )

        teacher = Teacher.objects.create(user=user)
        assignments = []
        for class_id, subject_id in zip(class_ids, subject_ids):

            if class_id and subject_id:

                cls = Class.objects.get(id=class_id)
                subj = Subject.objects.get(id=subject_id)

                TeacherAssignment.objects.get_or_create(
                    teacher=teacher,
                    class_assigned=cls,
                    subject_name=subj
                )
                assignments.append(f"{cls.name} → {subj.name}")


        return render(request, 'result/teacher_credential.html',{'teacher_name': f"{first_name} {last_name}",
                'username': username,
                'password': password,
                'assignments': assignments,
                'login_url': request.build_absolute_uri('/teacher/login/'),
            })
    return render(request, 'result/add_teacher.html', {'subjects': subjects,'classes': classes,})

@login_required(login_url='result:admin_login')
def delete_teacher(request, pk):
    if not request.user.is_staff:
        return redirect('result:dashboard')
    teacher = get_object_or_404(Teacher, pk=pk)
    if request.method == 'POST':
        teacher.user.delete()
        messages.success(request, 'Teacher deleted!')
        return redirect('result:teacher_list')
    return render(request, 'result/confirm_delete_teacher.html', {'teacher': teacher})

@login_required(login_url='result:admin_login')
def edit_teacher(request, pk):
    if not request.user.is_staff:
        return redirect('result:dashboard')

    teacher = get_object_or_404(Teacher, pk=pk)
    user = teacher.user

    subjects = Subject.objects.all()
    classes = Class.objects.all()

    if request.method == "POST":

        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        user.email = request.POST.get("email")
        user.save()

        class_ids = request.POST.getlist("assigned_class[]")
        subject_ids = request.POST.getlist("subject[]")

        TeacherAssignment.objects.filter(teacher=teacher).delete()

        for class_id, subject_id in zip(class_ids, subject_ids):
            TeacherAssignment.objects.get_or_create(
                teacher=teacher,
                class_assigned_id=class_id,
                subject_name_id=subject_id
            )
        return redirect("result:teacher_list")

    assignments = TeacherAssignment.objects.filter(teacher=teacher).select_related(
        'class_assigned', 'subject_name'
    )
    context = {
        'teacher': teacher,
        'user': teacher.user,
        'subjects': subjects,
        'classes': classes,
        'assignments': assignments,
    }

    return render(request, "result/edit_teacher.html", context)

@login_required(login_url='result:admin_login')
def publish_result(request):
    if not request.user.is_superuser:
        messages.error(request, "Access denied")
        return redirect('result:teacher_dashboard')
    
    result = Resultpublished.objects.all()
    # result.is_published = True
    # result.published_at = timezone.now()

    return render(request, 'result/publish_result.html', {'results': result})


@login_required(login_url='result:admin_login')
def publish_class(request, id):

    if not request.user.is_superuser:
      messages.error(request, "Access denied")
      return redirect('result:teacher_dashboard')
    
    result = Resultpublished.objects.get(id=id)
    result.is_published = True
    result.published_at = timezone.now()
    result.save()

    messages.success(request,f"{result.class_name.name} Result published successfully!")
    return redirect('result:publish_result')

@login_required(login_url='result:admin_login')
def publish_all_result(request):
    if not request.user.is_superuser:
        messages.error(request, "Access denied")
        return redirect('result:teacher_dashboard')
    Resultpublished.objects.update(
        is_published=True,
        published_at=timezone.now()
    )
    messages.success(request, "All Result publish Successfully!")
    return redirect('result:publish_result')

@login_required(login_url='result:admin_login')
def cancel_publish_class(request, class_id):

    if not request.user.is_superuser:
        messages.error(request, "Access denied")
        return redirect('result:teacher_dashboard')

    result = Resultpublished.objects.get(id=class_id)

    result.is_published = False
    result.published_at = None
    result.save()

    messages.success(request,f"{result.class_name.name} publish cancelled!")
    return redirect('result:publish_result')

@login_required(login_url='result:admin_login')
def cancel_all_result(request):

    if not request.user.is_superuser:
        messages.error(request, "Access denied")
        return redirect('result:teacher_dashboard')


    Resultpublished.objects.update(
        is_published=False,
        published_at=None
    )

    messages.success(request, "All result publish cancelled!")
    return redirect('result:publish_result')


@login_required(login_url='result:student_login')
def student_change_password(request):
    form = PasswordChangeForm(
        request.user,
        request.POST or None
    )
    for field in form.fields.values():
     field.widget.attrs.update({
        'class':'form-control'
    })
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(
            request,
            user
        )
        student = request.user.student_profile
        student.must_change_password = False
        student.save()

        messages.success(request, "Password changed successfully!")
        return redirect('result:student_dashboard')
    return render(request, 'student/student_change_password.html', {'form': form})

@login_required(login_url='result:student_login')
def password_setup(request):
    student = request.user.student_profile
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "keep":
            student.must_change_password = False
            student.save()
            return redirect(
                "result:student_dashboard"
            )
        elif action == "change":
            return redirect("result:student_change_password")
    return render(request, "student/password_setup.html")