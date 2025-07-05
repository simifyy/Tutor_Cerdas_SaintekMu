# chatbot/urls.py
from django.urls import path
from . import views # Impor views dari aplikasi chatbot ini
from .views import chat_interface, process_chat_message

app_name = 'chatbot' # Namespace untuk URL aplikasi chatbot

urlpatterns = [
    # Map URL root ('') di dalam aplikasi chatbot ke view chat_interface
    path('', views.chat_interface, name='chat_interface'),
    # URL untuk memproses pesan akan ditambahkan di sini nanti
    path('process_message/', views.process_chat_message, name='process_message'),
]