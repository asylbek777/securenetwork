from django import forms
from django.contrib.auth.models import User
from .models import Assignment, Schedule, AssignmentComment
from django import forms
from .models import Message
from django import forms
from django_otp.plugins.otp_totp.models import TOTPDevice
import re

class OTPVerificationForm(forms.Form):
    otp_token = forms.CharField(max_length=6, label="Введите код OTP")


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'border border-gray-300 p-2 rounded', 'placeholder': 'Пароль'}))
    password_confirm = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'border border-gray-300 p-2 rounded', 'placeholder': 'Подтвердите пароль'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'username': forms.TextInput(
                attrs={'class': 'border border-gray-300 p-2 rounded', 'placeholder': 'Имя пользователя'}),
            'email': forms.EmailInput(attrs={'class': 'border border-gray-300 p-2 rounded', 'placeholder': 'Email'}),
        }

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 8:
            raise forms.ValidationError("Пароль должен содержать минимум 8 символов.")
        if not re.search(r'[A-Za-z]', password):
            raise forms.ValidationError("Пароль должен содержать хотя бы одну букву.")
        if not re.search(r'[0-9]', password):
            raise forms.ValidationError("Пароль должен содержать хотя бы одну цифру.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise forms.ValidationError("Пароль должен содержать хотя бы один специальный символ (например, !@#$%^&*).")
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Пароли не совпадают")
        return cleaned_data


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'file', 'category']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('Общее', 'Общее'),

            ]),
        }

class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['title', 'date', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = AssignmentComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={'class': 'flex-1 border border-gray-300 p-2 rounded', 'placeholder': 'Напишите сообщение'}),
        }