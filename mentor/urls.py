# mentor/urls.py
from django.urls import path
from . import views 

app_name = 'mentor' 

urlpatterns = [
    path('', views.home_mentor, name='home'),

    path('materi/', views.list_modules, name='materi_module_list'),
    path('materi/modul/tambah/', views.add_module, name='tambah_modul'),
    path('materi/modul/edit/<slug:slug>/', views.edit_module, name='edit_modul'),
    path('materi/modul/hapus/<slug:slug>/', views.delete_module, name='hapus_modul'),
    path('materi/modul/<slug:module_slug>/', views.module_detail_mentor, name='module_detail_mentor'),
    path('materi/modul/<slug:module_slug>/tambah-topik/', views.add_topic, name='tambah_topik'),
    path('materi/topik/edit/<slug:slug>/', views.edit_topic, name='edit_topik'),
    path('materi/topik/hapus/<slug:slug>/', views.delete_topic, name='hapus_topik'),
    path('materi/topik/<slug:slug>/', views.topic_detail_mentor, name='topic_detail_mentor'),
    path('materi/topik/<slug:topic_slug>/tambah-pelajaran/', views.add_lesson, name='tambah_lesson'),
    path('materi/pelajaran/edit/<int:pk>/', views.edit_lesson, name='edit_lesson'),
    path('materi/pelajaran/hapus/<int:pk>/', views.delete_lesson, name='hapus_lesson'),
    path('materi/topik/<slug:topic_slug>/tambah-kuis/', views.add_quiz, name='tambah_kuis'),
    path('materi/kuis/edit/<int:pk>/', views.edit_quiz, name='edit_kuis'),
    path('materi/kuis/hapus/<int:pk>/', views.delete_quiz, name='hapus_kuis'),
    path('materi/kuis/<int:quiz_pk>/pertanyaan/', views.list_questions, name='list_questions'),
    path('materi/kuis/<int:quiz_pk>/pertanyaan/tambah/', views.add_question, name='tambah_question'),
    path('materi/pertanyaan/edit/<int:pk>/', views.edit_question, name='edit_question'),
    path('materi/pertanyaan/hapus/<int:pk>/', views.delete_question, name='hapus_question'),

    path('analisis/', views.analytics_dashboard, name='analisis'),
    path('analisis/user/<int:user_pk>/', views.user_activity_detail, name='analisis_user_detail'),

    path('profil/', views.mentor_profile, name='profile'),
    path('profil/edit/', views.edit_mentor_profile, name='profile_edit'),
]