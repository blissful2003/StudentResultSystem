from django import forms
from .models import Class, Subject, Student, Marks
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm as BasePasswordChangeForm


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['class_name', 'name', 'full_marks',
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

class MarksForm(forms.ModelForm):
    class Meta:
        model = Marks
        fields = ['student', 'subject',
                  'theory_obtained', 'practical_obtained']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'theory_obtained': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': '0'
            }),
            'practical_obtained': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': '0'
            }),
        }


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