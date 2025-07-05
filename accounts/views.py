# accounts/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction # Ditambahkan
# Impor semua form yang relevan dari forms.py
from .forms import (
    ProfileUpdateForm,
    RegistrationForm,
    CustomAuthenticationForm,
    MentorUserCreationForm, # Ditambahkan
    MentorApplicationForm   # Ditambahkan
)
# from django.contrib.auth import login 

# Import tambahan untuk Custom Login View
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
# from django.conf import settings
from .models import User 
from .models import MentorApplication

# --- View Registrasi (Kode Anda sebelumnya) ---
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Akun berhasil dibuat untuk {username}! Silakan Masuk.')
            return redirect('accounts:login') 
        else:
            pass
    else:
        form = RegistrationForm()

    context = {'form': form}
    return render(request, 'accounts/register.html', context)

# --- KODE BARU DIMULAI DI SINI ---
def register_mentor(request):
    if request.method == 'POST':
        user_form = MentorUserCreationForm(request.POST)
        application_form = MentorApplicationForm(request.POST, request.FILES)

        if user_form.is_valid() and application_form.is_valid():
            try:
                # Memastikan semua operasi database berhasil atau tidak sama sekali
                with transaction.atomic():
                    # 1. Buat user baru, tapi jangan simpan dulu (commit=False)
                    user = user_form.save(commit=False)
                    # Set user tidak aktif sampai lamarannya disetujui
                    user.is_active = True 
                    # Set nama depan dan belakang dari field full_name
                    full_name = application_form.cleaned_data.get('full_name')
                    parts = full_name.split(' ', 1)
                    user.first_name = parts[0]
                    user.last_name = parts[1] if len(parts) > 1 else ''
                    user.save() # Sekarang simpan user

                    # 2. Simpan data lamaran yang terhubung dengan user baru
                    application = application_form.save(commit=False)
                    application.user = user
                    application.save()
                
                messages.success(request, 'Lamaran Anda telah berhasil dikirim! Kami akan meninjau dan memberi kabar melalui email jika disetujui.')
                return redirect('accounts:login') # Arahkan ke halaman login

            except Exception as e:
                # Anda bisa log error 'e' di sini untuk debugging
                messages.error(request, 'Terjadi kesalahan saat memproses lamaran Anda.')
    else:
        user_form = MentorUserCreationForm()
        application_form = MentorApplicationForm()

    context = {
        'user_form': user_form,
        'application_form': application_form
    }
    return render(request, 'accounts/register_mentor.html', context)
# --- AKHIR KODE BARU ---

# --- View Profil (Kode Anda sebelumnya) ---
@login_required
def profile(request):
    context = {'user': request.user}
    return render(request, 'accounts/profile.html', context)

# --- View Edit Profil (Kode Anda sebelumnya) ---
@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user) 
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil Anda berhasil diperbarui.')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Terjadi kesalahan. Silakan periksa input Anda.')
    else:
        form = ProfileUpdateForm(instance=request.user)

    context = {'form': form}
    return render(request, 'accounts/edit_profile.html', context)


# --- Custom Login View (Kode Anda sebelumnya) ---
class CustomLoginView(LoginView):
    template_name = 'accounts/login.html' # Ganti jika nama template Anda berbeda
    authentication_form = CustomAuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        """
        Mengembalikan URL tujuan setelah login berhasil.
        Logika:
        1. Jika user adalah Pengajar -> Dashboard Mentor.
        2. Jika user adalah Pengguna biasa TAPI punya data lamaran:
           - Jika status PENDING/REJECTED -> Halaman Status Lamaran.
           - Jika status APPROVED (seharusnya role sudah jadi Pengajar) -> Dashboard Mentor.
        3. Jika user adalah Pengguna biasa (tanpa data lamaran) -> Halaman utama.
        """
        user = self.request.user

        # 1. Cek jika user adalah pengajar yang sudah disetujui
        if user.role == User.Role.TEACHER:
            return reverse_lazy('mentor:home')

        # 2. Cek jika user adalah pengguna biasa yang punya lamaran
        try:
            application = user.mentor_application
            # Jika punya lamaran, cek statusnya
            if application.status in ['PENDING', 'REVIEW', 'REJECTED']: # Tambahkan 'REVIEW'
                return reverse_lazy('accounts:application_status')
            elif application.status == 'APPROVED':
                # Ini sebagai fallback jika role belum terupdate
                return reverse_lazy('mentor:home')
        except MentorApplication.DoesNotExist:
            # 3. Jika user tidak punya lamaran, berarti pengguna biasa
            pass
        
        # Default redirect untuk pengguna biasa
        return reverse_lazy('core:index')
    
@login_required
def application_status(request):
    try:
        # Mengambil data lamaran yang terhubung dengan user yang sedang login
        application = request.user.mentor_application
    except MentorApplication.DoesNotExist:
        # Jika user tidak punya data lamaran, arahkan ke halaman utama
        # Ini sebagai pengaman saja
        return redirect('core:index')

    context = {
        'application': application
    }
    return render(request, 'accounts/application_status.html', context)