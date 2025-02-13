

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


@login_required
def room(request, room_name, receiver):
    try:
        # Verificar que el destinatario exista
        User.objects.get(username=receiver)
    except User.DoesNotExist:
        # Redirigir a la página principal si el destinatario no existe
        return redirect('index')

    return render(request, 'chat/room.html', {
        'room_name': room_name,
        'receiver': receiver,
    })
    
@login_required
def index(request):
    if request.method == 'POST':
        room_name = request.POST.get('room_name')
        receiver = request.POST.get('receiver')
        return redirect('room', room_name=room_name, receiver=receiver)
    return render(request, 'chat/index.html')

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