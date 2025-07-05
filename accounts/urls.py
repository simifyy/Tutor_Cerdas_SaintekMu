# accounts/urls.py
from django.urls import path, reverse_lazy
from . import views

from django.contrib.auth.views import (
    LogoutView,
    PasswordChangeView,
    PasswordChangeDoneView
)

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    # --- KODE BARU DI SINI ---
    path('register/mentor/', views.register_mentor, name='register_mentor'),

    path('login/', views.CustomLoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('lamaran/status/', views.application_status, name='application_status'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    path(
        'password_change/',
        PasswordChangeView.as_view(
            template_name='accounts/password_change_form.html',
            success_url=reverse_lazy('accounts:password_change_done')
        ),
        name='password_change'
    ),
    path(
        'password_change/done/',
        PasswordChangeDoneView.as_view(
            template_name='accounts/password_change_done.html'
        ),
        name='password_change_done'
    ),
]