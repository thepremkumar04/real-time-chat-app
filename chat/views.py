from django.shortcuts import render, redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .models import Message
from .serializers import MessageSerializer

# 1. Protect the chat view!
@login_required(login_url='login')
def index(request):
    # Pass the logged-in user's name to the HTML template
    return render(request, 'chat/index.html', {'username': request.user.username})

# 2. Add a Registration View
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # Auto-login after registering
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'chat/register.html', {'form': form})

# 3. Existing API View
@api_view(['GET'])
def message_history(request, room_name):
    messages = Message.objects.filter(room_name=room_name).order_by('-timestamp')[:50]
    messages = reversed(messages) 
    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)