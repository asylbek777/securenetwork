from django.db import models
from django.contrib.auth.models import User
from django_otp.plugins.otp_totp.models import TOTPDevice
from django.utils import timezone
from datetime import timedelta


class BlockedIP(models.Model):
    ip_address = models.GenericIPAddressField(unique=True)
    blocked_until = models.DateTimeField()

    def is_blocked(self):
        return self.blocked_until > timezone.now()

    def __str__(self):
        return f"IP {self.ip_address} заблокирован до {self.blocked_until}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_teacher = models.BooleanField(default=False)


    def __str__(self):
        return self.user.username

class Assignment(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    file = models.FileField(upload_to='assignments/', null=True, blank=True, verbose_name="Файл")
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignments', verbose_name="Учитель")
    category = models.CharField(max_length=100, default='Общее', verbose_name="Категория")  # Добавлено поле
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    def __str__(self):
        return self.title

class AssignmentComment(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username}: {self.content[:50]}'

class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    content = models.TextField(verbose_name="Сообщение")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Время")

    def __str__(self):
        return f'{self.user.username}: {self.content[:50]}'

class Schedule(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название")
    date = models.DateTimeField(verbose_name="Дата и время")
    description = models.TextField(verbose_name="Описание")
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='schedules', verbose_name="Учитель")

    def __str__(self):
        return self.title

class News(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Содержание")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")

    def __str__(self):
        return self.title