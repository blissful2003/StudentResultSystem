from django import forms
from .models import Class, Subject, Student, Marks, TeacherAssignment
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm as BasePasswordChangeForm

User = get_user_model()
class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['class_name', 'name','full_marks',
                  'theory_marks', 'practical_marks', 'pass_marks']
        widgets = {
            'class_name': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Mathematics, Science'
            }),
            'full_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '100'
            }),
            'theory_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '60'
            }),
            'practical_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '40'
            }),
            'pass_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '40'
            }),
        }


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'roll_number', 'first_name', 'last_name',
            'email', 'phone', 'gender', 'date_of_birth',
            'address', 'class_name',
            'parent_name', 'parent_phone', 'parent_email',
        ]
        widgets = {
            'roll_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3
            }),
            'class_name': forms.Select(attrs={'class': 'form-select'}),
            'parent_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Parent Full Name'
            }),
            'parent_phone': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Parent Phone Number'
            }),
            'parent_email': forms.EmailInput(attrs={
                'class': 'form-control', 'placeholder': 'Parent Email (optional)'
            }),
        }
    

class CSVUploadForm(forms.Form):
       class_name = forms.ModelChoiceField(
        queryset=Class.objects.all(),
        label="Select Class"
    )
csv_file = forms.FileField()

class MarksForm(forms.ModelForm):
    class Meta:
        model = Marks
        fields = ['theory_obtained', 'practical_obtained']
        widgets = {
            'theory_obtained': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
            'practical_obtained': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
        }

    def __init__(self, *args, **kwargs):
        self.subject = kwargs.pop('subject', None) 
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        theory = cleaned_data.get('theory_obtained') 
        practical = cleaned_data.get('practical_obtained') 

        subject = self.subject or (self.instance.subject if self.instance and self.instance.pk else None)
        if not subject:
            return cleaned_data

        if theory > subject.theory_marks:
            self.add_error('theory_obtained', f'Theory marks cannot exceed {subject.theory_marks}.')

        if practical > subject.practical_marks:
            self.add_error('practical_obtained', f'Practical marks cannot exceed {subject.practical_marks}.')

        total = theory + practical
        if total > subject.full_marks:
            raise forms.ValidationError(f'Total marks cannot exceed {subject.full_marks}.')

        return cleaned_data
    

class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})


class ClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ['name', 'section']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 10, 11, 12'
            }),
            'section': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: A, B (optional)'
            }),
        }


class PasswordChangeForm(BasePasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class TeacherAssignmentForm(forms.ModelForm):
    class Meta:
        model = TeacherAssignment
        fields = ['teacher', 'assigned_class', 'subject']            