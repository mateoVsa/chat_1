from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  
    path('<str:room_name>/<str:receiver>/', views.room, name='room'), 
  
]