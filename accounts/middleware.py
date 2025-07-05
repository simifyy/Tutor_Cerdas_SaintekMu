# accounts/middleware.py
from django.shortcuts import redirect
from django.urls import reverse
from .models import User, MentorApplication

class ApplicantStatusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Middleware hanya berjalan untuk user yang sudah login
        if request.user.is_authenticated:
            # Kita tidak ingin middleware ini mengganggu superuser atau pengajar yang sudah disetujui
            if request.user.is_superuser or request.user.role == User.Role.TEACHER:
                return self.get_response(request)

            # Cek apakah user ini adalah calon pengajar (punya data lamaran)
            try:
                application = request.user.mentor_application
                # Jika statusnya PENDING atau REVIEW, maka batasi aksesnya
                if application.status in ['PENDING', 'REVIEW']:
                    # Daftar URL yang BOLEH diakses oleh calon pengajar
                    allowed_paths = [
                        reverse('accounts:application_status'),
                        reverse('accounts:logout'),
                    ]
                    
                    # Kita juga perlu mengizinkan akses ke halaman admin (meskipun mereka tidak bisa login ke sana)
                    # dan path lain yang tidak termasuk dalam pembatasan (misal: file media/static).
                    # Jika path yang diakses tidak ada di 'allowed_paths' dan tidak berawalan '/admin/',
                    # maka alihkan pengguna.
                    if request.path not in allowed_paths and not request.path.startswith('/admin/'):
                        # Jika user mencoba akses URL lain, lempar kembali ke halaman status
                        return redirect('accounts:application_status')

            except MentorApplication.DoesNotExist:
                # Jika user tidak punya data lamaran, berarti dia pengguna biasa. Biarkan saja.
                pass
        
        # Lanjutkan request ke tujuan selanjutnya (view)
        response = self.get_response(request)
        return response