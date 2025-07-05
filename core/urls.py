# core/urls.py
from django.urls import path
from . import views # Impor views dari folder yang sama

app_name = 'core' # Namespace untuk URL (opsional tapi bagus)

urlpatterns = [
    # Map URL root (kosong '') di dalam aplikasi 'core' ke view 'index'
    path('', views.index, name='index'),
    path('mentoring/', views.mentor_list, name='mentor_list'),
    path('bantuan/', views.bantuan, name='bantuan'),
]