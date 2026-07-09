from ast import Return
import csv
from datetime import datetime, timezone
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
from result.utils import send_result_email
from .models import Teacher, TeacherAssignment, Subject, Class
from .models import Result, Student, Subject, Marks, Class, Teacher, TeacherAssignment, generate_student_id
from .forms import StudentForm, SubjectForm, MarksForm, ClassForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import get_user_model

User = get_user_model()

def admin_login(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
         return redirect('dashboard')
        else:
            return redirect('teacher_dashboard')
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user is not None:
            auth_login(request, user)
            if user.is_superuser:
             return redirect('dashboard')
            else:
                return redirect('teacher_dashboard')
        messages.error(request, 'Username and password incorrect!')
    return render(request, 'result/login.html')


def admin_logout(request):
    auth_logout(request)
    return redirect('login')


@login_required(login_url='login')
def dashboard(request):
    if not request.user.is_superuser:
        messages.error(request, "Access Denied!")
        return redirect('teacher_dashboard')

    return render(request, 'result/dashboard.html', {
        'total_students': Student.objects.count(),
        'total_subjects': Subject.objects.count(),
        'pass_count': Marks.objects.filter(is_pass=True).count(),
        'fail_count': Marks.objects.filter(is_pass=False).count(),
    })


@login_required(login_url='login')
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


@login_required(login_url='login')
def add_student(request):
    if request.method == "POST" and "upload_csv" in request.POST:
     class_id = request.POST.get("class_id")
     class_obj = Class.objects.get(id=class_id)
     csv_file = request.FILES["csv_file"]

    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            student.student_id = generate_student_id()
            username = student.student_id
            password = student.date_of_birth.strftime('%Y%m%d')
            if User.objects.filter(username=username).exists():
                messages.error(request, f'Username {username} already exists!')
                return render(request, 'result/add_student.html', {'form': form})
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
            messages.success(
                request,
                f'Student added! | Username: {username} | Password: {password}'
            )
            return redirect('student_list')
        else:
          messages.error(request, form.non_field_errors().as_text().replace("* ", ""))
          
    else:
        form = StudentForm()
    return render(request, 'result/add_student.html', {'form': form})


@login_required(login_url='login')
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
            return redirect('student_list')
    else:
        form = StudentForm(instance=student)
    return render(request, 'result/add_student.html', {'form': form, 'edit': True})


@login_required(login_url='login')
def delete_student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        if student.user:
            student.user.delete()
        student.delete()
        messages.success(request, 'Student deleted!')
        return redirect('student_list')
    return render(request, 'result/confirm_delete.html', {'student': student})

@login_required(login_url='login')
def upload_students(request):
    classes = Class.objects.all()
    if request.method == "POST":
        class_id = request.POST.get("class_id")
        csv_file = request.FILES["csv_file"]
        print(csv_file)
        selected_class = Class.objects.get(id=class_id)

        decoded_file = csv_file.read().decode("utf-8-sig").splitlines()
        reader = csv.DictReader(decoded_file)
        count=0

        for row in reader:
            if Student.objects.filter(class_name=selected_class, roll_number=row['roll_number']).exists():
                print("Roll already exits")
                continue

            if Student.objects.filter(phone=row['phone']).exists():
                print("Phone number already exit")
                continue
            #print(row['roll_number'], row['first_name'])
            student_id = generate_student_id()
            print(User)
            username = student_id
            password = row['date_of_birth'].replace("-", "")
            # if User.objects.filter(username=username).exists():
            #    print("Already exists:", username)
            # continue
            # print("USERNAME:", username)
            # print("EXISTS:", User.objects.filter(username=username).exists())
            user = User.objects.create(
                username=username,
                password=password,
                first_name=row['first_name'],
                last_name=row['last_name'],
                email=row['email'],
                role='student',
            )
            Student.objects.create(
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
                parent_email=row['parent_email'],
            )
            count += 1
            print("Student saved:", Student.first_name, Student.student_id)
            print("Total uploaded:", count)
    
        messages.success(request, "Students uploaded successfully!")
        return redirect('student_list')
    return render(request, "result/upload_student.html", {
        "classes": classes
    })


def download_student_credentials(request, class_id):
    students = Student.objects.filter(class_name_id=class_id).order_by('student_id')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="student_credentials.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'Student ID',
        'Username',
        'Password'
        'class'
    ])

    for student in students:
        writer.writerow([
            student.student_id,
            student.student_id,
            student.date_of_birth,
            student.class_name.class_name
        ])

    return response

@login_required(login_url='login')
def add_subject(request):
    form = SubjectForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Subject added successfully!')
        return redirect('dashboard')
    else:
         print(form.errors)
    return render(request, 'result/add_subject.html', {'form': form})


@login_required(login_url='login')
def admin_add_marks(request):
    form = MarksForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Marks added successfully!')
        return redirect('student_list')
    return render(request, 'result/add_marks.html', {'form': form})


@login_required(login_url='login')
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


@login_required(login_url='login')
def edit_marks(request, pk):
    mark = get_object_or_404(Marks, pk=pk)
    form = MarksForm(request.POST or None, instance=mark)
    if form.is_valid():
        form.save()
        messages.success(request, 'Marks updated successfully!')
        return redirect('student_result', pk=mark.student.pk)
    return render(request, 'result/add_marks.html', {'form': form, 'edit': True})


@login_required(login_url='login')
def subject_list(request):
    subjects = Subject.objects.all()
    return render(request, 'result/subject_list.html', {'subjects': subjects})


@login_required(login_url='login')
def edit_subject(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    form = SubjectForm(request.POST or None, instance=subject)
    if form.is_valid():
        form.save()
        messages.success(request, 'Subject updated successfully!')
        return redirect('subject_list')
    return render(request, 'result/add_subject.html', {'form': form, 'edit': True})


@login_required(login_url='login')
def delete_subject(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        subject.delete()
        messages.success(request, 'Subject deleted successfully!')
        return redirect('subject_list')
    return render(request, 'result/confirm_delete_subject.html', {'subject': subject})


@login_required(login_url='login')
def add_class(request):
    next_page = request.GET.get('next') or request.POST.get('next') or 'add_subject'

    form = ClassForm(request.POST or None)

    if form.is_valid():
        form.save()
        messages.success(request, 'Class added successfully!')
        return redirect(next_page)

    return render(request, 'result/add_class.html', {
        'form': form,
        'next': next_page
    })

@login_required(login_url='login')
def profile(request):
    return render(request, 'result/profile.html', {'user': request.user})


@login_required(login_url='login')
def change_password(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, 'Password changed successfully!')
        return redirect('profile')
    return render(request, 'result/change_password.html', {'form': form})


def student_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user and hasattr(user, 'student_profile'):
            auth_login(request, user)
            return redirect('student_dashboard')
        else:
            messages.error(request, 'Invalid username or password!')
    return render(request, 'student/login.html')


def student_logout(request):
    auth_logout(request)
    return redirect('student_login')


@login_required(login_url='student_login')
def student_dashboard(request):
    try:
        student = request.user.student_profile
    except:
        return redirect('student_login')
    my_marks = Marks.objects.filter(student=student)
    total_obtained = sum(m.marks_obtained for m in my_marks)
    total_full = sum(m.subject.full_marks for m in my_marks)
    overall_pct = round((total_obtained / total_full * 100) if total_full else 0, 2)

    class_students_qs = Student.objects.filter(class_name=student.class_name).order_by('roll_number')

    class_students = []
    for s in class_students_qs:
        s_marks = Marks.objects.filter(student=s)
        if s_marks.exists():
            status = 'Pass' if all(m.is_pass for m in s_marks) else 'Fail'
        else:
            status = 'Pending'
        s.status = status
        class_students.append(s)

    return render(request, 'student/dashboard.html', {
        'student': student,
        'my_marks': my_marks,
        'total_obtained': total_obtained,
        'total_full': total_full,
        'overall_pct': overall_pct,
        'class_students': class_students,
    })

@login_required(login_url='student_login')
def student_own_result(request):
    try:
        student = request.user.student_profile
    except:
        return redirect('student_login')
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

@login_required
def student_result_view(request):
    student = get_object_or_404(Student, user=request.user)
    
    
    marks_list = Marks.objects.filter(student=student, is_published=True)
    
    if not marks_list.exists():
        return render(request, 'student/result.html', {
            'student': student,
            'not_published': True,
        })
    
    overall_pass = all(m.is_pass for m in marks_list)
    total_obtained = sum(m.marks_obtained for m in marks_list)
    total_full = sum(m.subject.full_marks for m in marks_list)
    
    
    classmates = Student.objects.filter(class_name=student.class_name).order_by('roll_number')
    
    classmates_data = []
    for classmate in classmates:
        classmate_marks = Marks.objects.filter(student=classmate, is_published=True)
        if classmate_marks.exists():
            classmate_overall_pass = all(m.is_pass for m in classmate_marks)
            status = 'Pass' if classmate_overall_pass else 'Fail'
        else:
            classmate_overall_pass = None
            status = 'Pending'
        
        classmates_data.append({
            'name': f"{classmate.first_name} {classmate.last_name}",
            'roll_number': classmate.roll_number,
            'is_pass': classmate_overall_pass,
            'status': status,
            'is_me': classmate == student,
        })
    
    context = {
        'student': student,
        'marks_list': marks_list,
        'overall_status': 'Pass' if overall_pass else 'Fail',
        'total_obtained': total_obtained,
        'total_full': total_full,
        'classmates_data': classmates_data,
    }
    return render(request, 'student/result.html', context)

def publish_results(request, class_id):
    results = Result.objects.filter(student_class_id=class_id, is_published=False)
    count = results.count()
    results.update(is_published=True, published_at=timezone.now())
    
    
    send_result_email(class_id)   
    
    messages.success(request, f"{count} student ko result publish vayo!")
    return redirect('admin_class_results', class_id=class_id)

def teacher_login(request):
    if request.method =='POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user and hasattr(user, 'teacher'):
            auth_login(request, user)
            return redirect('teacher_dashboard')
        else:
            messages.error(request, 'Invalid username and password!')
    return render(request, 'teacher/login.html')

def teacher_logout(request):
    auth_logout(request)
    return redirect('teacher_login')


@teacher_required
def teacher_dashboard(request):
    teacher = request.user.teacher
    assignments = TeacherAssignment.objects.filter(teacher=teacher).select_related('class_assigned', 'subject_name')

    dashboard_data = []
    for assignment in assignments:
        students = Student.objects.filter(
            class_name=assignment.class_assigned
        ).order_by('roll_number')

        student_data = []
        for student in students:
            mark = Marks.objects.filter(
                student=student, subject=assignment.subject_name
            ).first()
            student_data.append({
                'student': student,
                'mark': mark,
                'status': 'Pass' if mark and mark.is_pass else ('Fail' if mark else 'Not Added'),
            })
        dashboard_data.append({
            'assignment': assignment,
            'students': student_data,
        })

    return render(request, 'teacher/dashboard.html', {'dashboard_data': dashboard_data})

    return render(request, "teacher/profile.html", context)
@teacher_required
def add_mark(request, student_id, subject_id, class_id):
    teacher = request.user.teacher

    assignment = get_object_or_404(
        TeacherAssignment, teacher=teacher, class_assigned_id=class_id, subject_name_id=subject_id
    )
    student = get_object_or_404(Student, id=student_id, class_name_id=class_id)
    subject = assignment.subject_name

    mark_instance = Marks.objects.filter(student=student, subject=subject).first()

    if request.method == 'POST':
        form = MarksForm(request.POST, instance=mark_instance)
        if form.is_valid():
            mark = form.save(commit=False)
            mark.student = student
            mark.subject = subject
            mark.save()
            messages.success(request, "Marks saved successfully.")
            return redirect('teacher_dashboard')
    else:
        form = MarksForm(instance=mark_instance)

    return render(request, 'teacher/add_mark.html', {'form': form, 'student': student, 'subject': subject})
    

@teacher_required
def view_mark(request, mark_id):
    teacher = request.user.teacher
    mark = get_object_or_404(Marks, id=mark_id)
    is_authorized = TeacherAssignment.objects.filter(teacher=teacher, subject_name=mark.subject).exists()
    if not is_authorized:
        messages.error(request, "Unauthorized.")
        return redirect('teacher_dashboard')
    return render(request, 'teacher/view_mark.html', {'mark': mark})


@teacher_required
def edit_mark(request, mark_id):
    teacher = request.user.teacher
    mark = get_object_or_404(Marks, id=mark_id)

    is_authorized = TeacherAssignment.objects.filter(teacher=teacher, subject_name=mark.subject).exists()
    if not is_authorized:
        messages.error(request, "Unauthorized.")
        return redirect('teacher_dashboard')

    if request.method == 'POST':
        form = MarksForm(request.POST, instance=mark)
        if form.is_valid():
            form.save()
            messages.success(request, "Marks updated successfully.")
            return redirect('teacher_dashboard')
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
        return redirect('teacher_dashboard')

    mark.delete()

    messages.success(request, "Marks deleted successfully.")
    return redirect('teacher_dashboard')

def generate_password(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

@login_required(login_url='login')
def teacher_list(request):
    if not request.user.is_staff:
        return redirect('dashboard')
    teachers = Teacher.objects.select_related('user').prefetch_related('assignments__subject_name','assignments__class_assigned')
    return render(request, 'result/teacher_list.html', {'teachers': teachers})

@login_required(login_url='login')
def add_teacher(request):
    if not request.user.is_staff:
        return redirect('dashboard')

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

@login_required(login_url='login')
def delete_teacher(request, pk):
    if not request.user.is_staff:
        return redirect('dashboard')
    teacher = get_object_or_404(Teacher, pk=pk)
    if request.method == 'POST':
        teacher.user.delete()
        messages.success(request, 'Teacher deleted!')
        return redirect('teacher_list')
    return render(request, 'result/confirm_delete_teacher.html', {'teacher': teacher})

@login_required(login_url='login')
def edit_teacher(request, pk):
    if not request.user.is_staff:
        return redirect('dashboard')

    teacher = get_object_or_404(Teacher, pk=pk)
    user = teacher.user

    assignments = TeacherAssignment.objects.filter(teacher=teacher)

    subjects = Subject.objects.all()
    classes = Class.objects.all()

    if request.method == "POST":

        
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        user.email = request.POST.get("email")
        user.save()

        subject_ids = request.POST.getlist("subjects")
        class_ids = request.POST.getlist("assigned_classes")

        
        TeacherAssignment.objects.filter(teacher=teacher).delete()

    
        selected_subjects = Subject.objects.filter(id__in=subject_ids)
        selected_classes = Class.objects.filter(id__in=class_ids)

        for cls in selected_classes:
            for subj in selected_subjects:
                TeacherAssignment.objects.create(
                    teacher=teacher,
                    class_assigned=cls,
                    subject_name=subj,
                )

        return redirect("teacher_list")

    context = {
        "teacher": teacher,
        "user": user,
        "subjects": subjects,
        "classes": classes,
        "assignments": assignments,
    }

    return render(request, "result/edit_teacher.html", context)
