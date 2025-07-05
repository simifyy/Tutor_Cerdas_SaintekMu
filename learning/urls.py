print(">>> [DEBUG] Sedang memuat learning/urls.py...")
# learning/urls.py
from django.urls import path, reverse_lazy
from . import views
from .views import (
    ModuleListView, 
    ModuleDetailView, 
    LessonDetailView,
    mark_lesson_complete, 
    take_quiz, 
    quiz_result,
    take_pretest,       
    pretest_result,     
    pretest_history,    
    quiz_history        
)

# TEST SIMPAN FILE PUKUL [WAKTU SEKARANG]
app_name = 'learning'

urlpatterns = [
    path('', views.ModuleListView.as_view(), name='module_list'),
    path('<slug:slug>/', views.ModuleDetailView.as_view(), name='module_detail'),
    path('topic/<slug:topic_slug>/pretest/', views.take_pretest, name='take_pretest'),
    path('pretest/result/<int:attempt_id>/', views.pretest_result, name='pretest_result'),
    path('topic/<slug:topic_slug>/pretest/history/', views.pretest_history, name='pretest_history'),
    path('<slug:module_slug>/<slug:topic_slug>/quiz/', views.take_quiz, name='take_quiz'),
    path('attempt/<int:attempt_id>/result/', views.quiz_result, name='quiz_result'),
    path('quiz/<int:quiz_pk>/history/', views.quiz_history, name='quiz_history'),

    path('lesson/<slug:lesson_slug>/complete/', views.mark_lesson_complete, name='mark_lesson_complete'),
    path('<slug:module_slug>/<slug:topic_slug>/<slug:slug>/', views.LessonDetailView.as_view(), name='lesson_detail'),
]