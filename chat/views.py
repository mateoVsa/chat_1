from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db.models import Q  # Importar Q para consultas complejas
from .models import ChatRoom, Message
from .forms import ChatRoomForm


# Verificar si el usuario es administrador o staff
def is_admin(user):
    return user.is_staff or user.is_superuser


# Vista para crear salas de chat (solo para administradores)
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
    # Verificar si el room_name es un usuario (chat individual)
    try:
        user = User.objects.get(username=room_name)
        is_private_chat = True
    except User.DoesNotExist:
        is_private_chat = False

    if is_private_chat:
        # Verificar que el usuario tenga permiso para chatear
        if not (request.user.is_staff or request.user.is_superuser or user.is_staff or user.is_superuser):
            return redirect('index')  # Redirigir si no tiene permiso
    else:
        # Verificar que el usuario tenga acceso a la sala
        try:
            chat_room = ChatRoom.objects.get(name=room_name, allowed_users=request.user)
        except ChatRoom.DoesNotExist:
            return redirect('index')  # Redirigir si no tiene acceso

    # Recuperar mensajes antiguos
    if is_private_chat:
        # Mensajes de un chat individual
        messages = Message.objects.filter(
            (Q(sender=request.user) & Q(receiver__username=room_name)) |
            (Q(sender__username=room_name) & Q(receiver=request.user))
        ).order_by('timestamp')
    else:
        # Mensajes de un chat grupal
        messages = Message.objects.filter(
            receiver__username=room_name
        ).order_by('timestamp')

    return render(request, 'chat/room.html', {
        'room_name': room_name,
        'receiver': receiver,  # Pasar el receiver al template
        'is_private_chat': is_private_chat,  # Indicar si es un chat individual
        'messages': messages,  # Pasar los mensajes antiguos al template
    })
# Vista para la página principal del chat
@login_required
def index(request):
    # Obtener las salas a las que el usuario tiene acceso
    chat_rooms = ChatRoom.objects.filter(allowed_users=request.user)

    # Obtener la lista de usuarios
    if request.user.is_staff or request.user.is_superuser:
        # Los administradores ven todos los usuarios
        users = User.objects.all()
    else:
        # Los usuarios normales solo ven a los usuarios del staff
        users = User.objects.filter(is_staff=True)

    return render(request, 'chat/index.html', {
        'chat_rooms': chat_rooms,
        'users': users,
    })


# Vista para el registro de usuarios
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})