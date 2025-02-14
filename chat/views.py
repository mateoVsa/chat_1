

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import ChatRoom,Message
from .forms import ChatRoomForm


def is_admin(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_admin)
def create_chat_room(request):
    if request.method == 'POST':
        form = ChatRoomForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('index')
        form = ChatRoomForm()
    return render(request, 'chat/create_chat_room.html', {'form': form})

@login_required
def room(request, room_name, receiver):
    # Verificar si el room_name es un usuario (chat individual)
    try:
        user = User.objects.get(username=room_name)
        is_private_chat = True
    except User.DoesNotExist:
        is_private_chat = False

    if is_private_chat:
        # verificar que el usuario tenga permiso para chatear
        if not (request.user.is_staff or request.user.is_superuser or user.is_staff or user.is_superuser):
            return redirect('index')  # Redirigir si no tiene permiso
    else:
        # verificar que el usuario tenga acceso a la sala
        try:
            chat_room = ChatRoom.objects.get(name=room_name, allowed_users=request.user)
        except ChatRoom.DoesNotExist:
            return redirect('index')  # Redirigir si no tiene acceso

    # Recuperar mensajes antiguos
    if is_private_chat:
        # Mensajes de un chat individual
        messages = Message.objects.filter(
            sender__username__in=[request.user.username, room_name],
            receiver__username__in=[request.user.username, room_name]
        ).order_by('timestamp')
    else:
        # Mensajes de un chat grupal
        messages = Message.objects.filter(
            receiver__username=room_name
        ).order_by('timestamp')

    return render(request, 'chat/room.html', {
        'room_name': room_name,
        'receiver': receiver,
        'is_private_chat': is_private_chat,  # Indicar si es un chat individual
        'messages': messages,  # Pasar los mensajes antiguos al template
    })
    
@login_required
def index(request):
    chat_rooms = ChatRoom.objects.filter(allowed_users=request.user)
    
    if request.user.is_staff or request.user.is_superuser:
                users = User.objects.all()
    else:
                users = User.objects.filter(is_staff=True)
    return render(request, 'chat/index.html', {'chat_rooms': chat_rooms,'users':users})

def signup(request):
    if request.method=='POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request,user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html',{'form':form})


