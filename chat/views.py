from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib import messages
from .models import ChatRoom, Message
from .forms import ChatRoomForm


# Verificar si el usuario es administrador o staff
def is_admin(user):
    return user.is_staff or user.is_superuser


# Custom logout para cerrar sesión del usuario
def custom_logout(request):
    logout(request)
    return redirect('login')


# Vista para crear salas de chat (solo admins)
@login_required
@user_passes_test(is_admin)
def create_chat_room(request):
    if request.method == 'POST':
        form = ChatRoomForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = ChatRoomForm()
    return render(request, 'chat/create_chat_room.html', {'form': form})


# Vista para la sala de chat
@login_required
def room(request, room_name, receiver):
    if request.user.is_staff or request.user.is_superuser:
        users = User.objects.exclude(username=request.user.username)  # Admins ven a todos
    else:
        users = User.objects.filter(is_staff=True)  # Usuarios normales solo ven staff y admin

    try:
        user = User.objects.get(username=room_name)
        is_private_chat = True
    except User.DoesNotExist:
        is_private_chat = False

    if is_private_chat:
        messages_list = Message.objects.filter(
            (Q(sender=request.user) & Q(receiver__username=room_name)) |
            (Q(sender__username=room_name) & Q(receiver=request.user))
        ).order_by('timestamp')
        for msg in messages_list:
            msg.formatted_time = msg.timestamp.strftime("%H:%M;%S")
    else:
        messages_list = Message.objects.filter(receiver__username=room_name).order_by('timestamp')

    return render(request, 'chat/room.html', {
        'room_name': room_name,
        'receiver': receiver,
        'is_private_chat': is_private_chat,
        'messages': messages_list,
        'users': users,  # Se envía la lista de usuarios al template
    })


# Vista principal del chat
@login_required
def index(request):
    chat_rooms = ChatRoom.objects.filter(allowed_users=request.user)

    if request.user.is_staff or request.user.is_superuser:
        users = User.objects.exclude(username=request.user.username)  # Admins ven a todos
    else:
        users = User.objects.filter(is_staff=True)  # Usuarios normales solo ven staff y admin

    return render(request, 'chat/index.html', {
        'chat_rooms': chat_rooms,
        'users': users,
    })

# Vista para el registro de usuarios con validación de contraseña
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Las contraseñas no coinciden. Intente nuevamente.")
        elif form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, "Intente de nuevo.")

    else:
        form = UserCreationForm()

    return render(request, 'registration/signup.html', {'form': form})


# Vista personalizada de login con mensaje de error
def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            messages.success(request, "Inicio de sesión exitoso")
            return redirect('index')
        else:
            messages.error(request, "Credenciales incorrectas. Intente de nuevo.")

    return render(request, 'registration/login.html')