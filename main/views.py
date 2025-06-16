from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Assignment, Schedule, Message, Profile, AssignmentComment, News
from .forms import AssignmentForm, ScheduleForm, RegistrationForm, CommentForm, MessageForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django_otp.plugins.otp_totp.models import TOTPDevice
from .forms import OTPVerificationForm
from django_otp import match_token
from functools import wraps
from django_otp import devices_for_user
import qrcode
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from .ai_model import predict_brute_force
import time
import subprocess
from io import BytesIO
import base64


def otp_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('otp_verified') and devices_for_user(request.user, confirmed=True):
            return redirect('verify_otp')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

import logging
logger = logging.getLogger('django')


def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
@otp_required
def home(request):
    category = request.GET.get('category', '')
    assignments = Assignment.objects.all() if not category else Assignment.objects.filter(category=category)
    schedules = Schedule.objects.all()[:5]
    news_items = News.objects.all().order_by('-created_at')[:2]
    profile = Profile.objects.get_or_create(user=request.user)[0]
    categories = Assignment.objects.values_list('category', flat=True).distinct()
    return render(request, 'home.html', {
        'assignments': assignments,
        'schedules': schedules,
        'news_items': news_items,
        'profile': profile,
        'categories': categories,
        'selected_category': category
    })


@login_required
def setup_otp(request):
    user = request.user
    # Проверяем, есть ли неподтверждённое устройство, или создаём новое
    try:
        device = TOTPDevice.objects.get(user=user, name='default', confirmed=False)
    except TOTPDevice.DoesNotExist:
        device = TOTPDevice.objects.create(user=user, name='default', confirmed=False)

    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            token = form.cleaned_data['otp_token']
            if device.verify_token(token):
                device.confirmed = True
                device.save()
                request.session['otp_verified'] = True
                return redirect('home')
            else:
                form.add_error('otp_token', 'Неверный код OTP')
    else:
        form = OTPVerificationForm()

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(device.config_url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
    qr_url = f"data:image/png;base64,{qr_image}"

    return render(request, 'setup_otp.html', {'form': form, 'qr_url': qr_url})


@login_required
def verify_otp(request):
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            token = form.cleaned_data['otp_token']
            if match_token(request.user, token):
                request.session['otp_verified'] = True
                return redirect('home')
            else:
                form.add_error('otp_token', 'Неверный код OTP')
    else:
        form = OTPVerificationForm()
    return render(request, 'verify_otp.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            Profile.objects.create(user=user)
            login(request, user)
            return redirect('setup_otp')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

@login_required
@otp_required
def chat(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.user = request.user
            message.save()
            return redirect('chat')
    else:
        form = MessageForm()
    messages = Message.objects.all().order_by('timestamp')
    return render(request, 'chat.html', {'form': form, 'messages': messages})

@login_required
@otp_required
def upload_assignment(request):
    profile = Profile.objects.get(user=request.user)
    if not profile.is_teacher:
        return redirect('home')  # Если не учитель, перенаправляет на /home/
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.teacher = request.user
            assignment.save()
            return redirect('home')
    else:
        form = AssignmentForm()
    return render(request, 'upload_assignment.html', {'form': form})

@login_required

def schedule(request):
    profile = Profile.objects.get(user=request.user)
    if not profile.is_teacher:
        return redirect('home')  # Если не учитель, перенаправляет на /home/
    if request.method == 'POST':
        form = ScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.teacher = request.user
            schedule.save()
            return redirect('home')
    else:
        form = ScheduleForm()
    schedules = Schedule.objects.all()
    return render(request, 'schedule.html', {'form': form, 'schedules': schedules})

@login_required

def assignment_detail(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.assignment = assignment
            comment.save()
            return redirect('assignment_detail', assignment_id=assignment.id)
    else:
        form = CommentForm()
    comments = assignment.comments.all()
    return render(request, 'assignment_detail.html', {'assignment': assignment, 'form': form, 'comments': comments})

@login_required

def news(request):
    news_items = News.objects.all().order_by('-created_at')
    return render(request, 'news.html', {'news_items': news_items})

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response




from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

@method_decorator(login_required, name='dispatch')
class ChatBotView(APIView):
    def post(self, request):
        user_input = request.data.get('user_input')
        if not user_input:
            return Response({'bot_response': 'Пожалуйста, введите вопрос.'}, status=status.HTTP_400_BAD_REQUEST)

        user_input = user_input.lower()
        responses = {
            'привет': 'Здравствуйте, чем могу помочь?',
            'что это за платформа': 'Это платформа показывает пример методики разработки защищенной корпоративной сети.',
            'как загрузить задание': 'Перейдите на страницу "Загрузить задание" и следуйте инструкциям.',
            'как посмотреть расписание': 'Перейдите на страницу "Расписание", чтобы увидеть актуальное расписание.',
            'где найти новости': 'Новости доступны на странице "Новости", обновляются регулярно.',
            'как работает чат': 'Введите вопрос в поле ниже, и я постараюсь помочь. Отправьте сообщение кнопкой "Отправить".',
            'что такое безопасность сети': 'Безопасность сети — это защита данных и систем от несанкционированного доступа с помощью технологий и процедур.',
            'как зарегистрироваться': 'Нажмите на кнопку "Начать сейчас" и следуйте инструкциям для регистрации.',
            'где скачать файлы': 'Если файл доступен, ссылка на скачивание будет в разделе заданий рядом с описанием.',
            'как выйти из аккаунта': 'Нажмите на ссылку "Выйти" в правом верхнем углу, чтобы завершить сеанс.',
        }
        bot_response = responses.get(user_input, "Извините, я не понимаю ваш вопрос.")
        return Response({'bot_response': bot_response}, status=status.HTTP_200_OK)

# Хранение данных о попытках входа
attempts_data = {}

import logging

logger = logging.getLogger(__name__) # for ip check

# Настройка логирования
logging.basicConfig(
    filename="model_input_debug.log",  # Файл для записи логов
    level=logging.DEBUG,  # Уровень логирования
    format="%(asctime)s - %(message)s"  # Формат записи
)


import time
import logging
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django import forms
from django.utils import timezone
from django_otp import devices_for_user
from main.models import BlockedIP

# Настройка логирования
logger = logging.getLogger(__name__)

# Глобальный словарь для попыток входа
attempts_data = {}

# Форма логина
class LoginForm(forms.Form):
    username = forms.CharField(max_length=100, label="Username")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")

def get_client_ip(request):
    """Получить IP-адрес клиента."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

def predict_brute_force(model_input):
    """Прогнозировать брутфорс (заглушка)."""
    count, time_diff, ip_changes = model_input
    return count > 5 or ip_changes > 2  # Пример логики

from datetime import datetime, timedelta
from django.utils import timezone
from main.models import BlockedIP

def block_ip(ip_address, block_duration=30):
    """Блокировать IP-адрес на указанное время (в минутах)."""
    logger.warning(f"Попытка блокировки IP {ip_address} на {block_duration} минут")
    try:
        # Вычисляем время окончания блокировки
        blocked_until = timezone.now() + timedelta(minutes=block_duration)
        # Пытаемся обновить или создать запись
        blocked_ip, created = BlockedIP.objects.update_or_create(
            ip_address=ip_address,
            defaults={'blocked_until': blocked_until}
        )
        if created:
            logger.info(f"Новый IP заблокирован: {ip_address}")
        else:
            logger.info(f"Обновлена блокировка IP: {ip_address}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при блокировке IP {ip_address}: {str(e)}")
        return False

def custom_login(request):
    """Обработка входа с проверкой брутфорса и 2FA."""
    form = LoginForm()
    ip_address = get_client_ip(request)

    # Проверка, заблокирован ли IP
    try:
        blocked_ip = BlockedIP.objects.get(ip_address=ip_address)
        if blocked_ip.blocked_until and blocked_ip.blocked_until > timezone.now():
            return render(request, 'login.html', {
                'form': form,
                'error': 'Ваш IP-адрес заблокирован. Попробуйте позже.'
            })
    except BlockedIP.DoesNotExist:
        pass

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            current_time = time.time()

            # Логирование попытки
            logger.debug(f"Попытка входа: пользователь {username}, IP {ip_address}")

            # Обновление попыток
            user_attempts = attempts_data.get(username, {
                "count": 0,
                "last_time": current_time,
                "ip_changes": 0,
                "last_ip": ip_address
            })
            if user_attempts["last_ip"] != ip_address:
                user_attempts["ip_changes"] += 1
            time_diff = current_time - user_attempts["last_time"]
            user_attempts["count"] += 1
            user_attempts["last_time"] = current_time
            user_attempts["last_ip"] = ip_address
            attempts_data[username] = user_attempts

            # Данные для модели
            model_input = [user_attempts["count"], time_diff, user_attempts["ip_changes"]]
            logger.debug(f"Данные модели: попытки={model_input[0]}, время={model_input[1]:.2f}с, IP_смены={model_input[2]}")
            print(f"Пользователь: {username}")
            print(f"Количество попыток входа: {model_input[0]}")
            print(f"Время между попытками входа: {model_input[1]:.2f} секунд")
            print(f"Частота смены IP-адреса: {model_input[2]}")
            # Проверка брутфорса
            if user_attempts["count"] <= 4 or time_diff < 1:
                is_attack = False
            else:
                is_attack = predict_brute_force(model_input)

            if is_attack:
                block_ip(ip_address, block_duration=30)
                return render(request, 'login.html', {
                    'form': form,
                    'error': 'Обнаружена попытка brute force атаки! Ваш IP-адрес заблокирован.'
                })

            # Аутентификация
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                devices = list(devices_for_user(user, confirmed=True))
                if devices:
                    request.session['otp_verified'] = False
                    return redirect('verify_otp')
                return redirect('home')
            else:
                logger.error(f"Неудачная попытка входа: {username}, IP {ip_address}")
                return render(request, 'login.html', {
                    'form': form,
                    'error': 'Неверный логин или пароль.'
                })
        else:
            return render(request, 'login.html', {
                'form': form,
                'error': 'Некорректные данные формы.'
            })

    return render(request, 'login.html', {'form': form})

# def custom_login(request):
#
#
#     ip_address = request.META.get('REMOTE_ADDR')
#     print(f"Попытка входа с IP-адреса: {ip_address}") # for ip check
#     #logging.debug(f"Пользователь: {ip_address}")
#
#     global attempts_data
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         password = request.POST.get('password')
#
#         # Получение IP пользователя
#         ip_address = get_client_ip(request)
#         current_time = time.time()
#
#         # Получаем или инициализируем данные о пользователе
#         user_attempts = attempts_data.get(username, {
#             "count": 0, "last_time": current_time, "ip_changes": 0, "last_ip": ip_address
#         })
#
#         # Проверяем смену IP
#         if user_attempts["last_ip"] != ip_address:
#             user_attempts["ip_changes"] += 1
#
#         # Обновляем попытки
#         time_diff = current_time - user_attempts["last_time"]
#         user_attempts["count"] += 1
#         user_attempts["last_time"] = current_time
#         user_attempts["last_ip"] = ip_address
#
#         attempts_data[username] = user_attempts
#
#         # Готовим данные для модели
#         model_input = [
#             user_attempts["count"],  # Количество попыток входа
#             time_diff,  # Время между попытками входа
#             user_attempts["ip_changes"]  # Частота смены IP-адреса
#         ]
#
#         # Логирование данных
#         # logging.debug("Передаваемые в модель данные:")
#         # logging.debug(f"Пользователь: {username}")
#         # logging.debug(f"Количество попыток входа: {model_input[0]}")
#         # logging.debug(f"Время между попытками входа: {model_input[1]:.2f} секунд")
#         # logging.debug(f"Частота смены IP-адреса: {model_input[2]}")
#         print("Передаваемые в модель данные:")
#         print(f"Пользователь: {username}")
#         print(f"Количество попыток входа: {model_input[0]}")
#         print(f"Время между попытками входа: {model_input[1]:.2f} секунд")
#         print(f"Частота смены IP-адреса: {model_input[2]}")
#
#         # Проверка на атаку
#         if user_attempts["count"] <= 4 or time_diff < 1:
#             is_attack = False  # Не считать атакой, если слишком мало попыток
#         else:
#             is_attack = predict_brute_force(model_input)
#
#         if is_attack:
#             # Блокировка IP-адреса на 30 минут при атаке
#             block_ip(ip_address, block_duration=30)
#             #video_path = "/home/asylzhan/Desktop/atack.mp4"
#             #subprocess.run(["parole", video_path])
#             #return redirect('/')
#             return render(request, 'login.html', {'form': None, 'error': 'Обнаружена попытка brute force атаки! Ваш IP-адрес заблокирован.'})
#
#         # Попытка входа
#         user = authenticate(request, username=username, password=password)
#         if user is not None:
#             login(request, user)
#             return redirect('/')
#         else:
#             return render(request, 'login.html', {'form': None, 'error': 'Неверный логин или пароль.'})
#
#     return render(request, 'login.html', {'form': None})
#
# def get_client_ip(request):
#     x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
#     if x_forwarded_for:
#         ip = x_forwarded_for.split(',')[0]
#     else:
#         ip = request.META.get('REMOTE_ADDR')
#     return ip
# from django.utils import timezone
# from datetime import timedelta
# from .models import BlockedIP
#
# def is_ip_blocked(ip_address):
#     try:
#         blocked_ip = BlockedIP.objects.get(ip_address=ip_address)
#         return blocked_ip.is_blocked()
#     except BlockedIP.DoesNotExist:
#         return False
#
# def block_ip(ip_address, block_duration=30):
#     blocked_until = timezone.now() + timedelta(minutes=block_duration)
#     BlockedIP.objects.create(ip_address=ip_address, blocked_until=blocked_until)