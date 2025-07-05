# core/views.py
from pyexpat.errors import messages
from django.shortcuts import render, redirect, reverse 
from django.db.models import Count 
from django.contrib.auth.decorators import login_required 
from django.contrib.auth.views import LoginView # Import LoginView standar
from django.urls import reverse_lazy
# from django.conf import settings # Import jika perlu akses settings

# Impor model dari aplikasi lain
# Pastikan path impor ini sesuai dengan struktur proyek Anda
try:
    from accounts.models import User # Model User kustom Anda
    # Impor form kustom untuk login (jika belum)
    from accounts.forms import CustomAuthenticationForm 
except ImportError:
    # Fallback jika struktur berbeda atau model belum siap
    # Ini akan menyebabkan error jika view yang butuh User/CustomAuth dipanggil
    # Sebaiknya pastikan impor di atas berhasil
    from django.contrib.auth.models import User 
    from django.contrib.auth.forms import AuthenticationForm as CustomAuthenticationForm
    print("WARNING: Could not import custom User model or CustomAuthenticationForm from accounts app.")

# Impor model lain yang dibutuhkan
try:
    from learning.models import Module, Topic, Lesson, UserLessonProgress, Quiz, QuizAttempt 
except ImportError:
    Module = Topic = Lesson = UserLessonProgress = Quiz = QuizAttempt = None # Placeholder jika app learning belum ada
    print("WARNING: Could not import models from learning app.")
try:
    from articles.models import Article
except ImportError:
    Article = None # Placeholder jika app articles belum ada
    print("WARNING: Could not import Article model from articles app.")


def index(request):
    """ 
    Menampilkan homepage publik (jika anonim) atau dashboard user biasa 
    (jika login & bukan TEACHER). Mentor akan di-redirect.
    """
    if request.user.is_authenticated:
        # Cek Role Pengguna (Pastikan atribut 'role' dan Enum/konstanta 'Role.TEACHER' ada di model User Anda)
        try:
            is_teacher = hasattr(request.user, 'role') and request.user.role == User.Role.TEACHER
        except AttributeError: # Jika User.Role tidak ada / error
            is_teacher = False 
            print("WARNING: Could not check User.Role.TEACHER.")

        if is_teacher:
            # Jika user adalah Teacher, arahkan ke dashboard mentor
            return redirect(reverse('mentor:home')) # Pastikan URL name ini benar
        else:
            # --- Logika untuk Pengguna Login (Dashboard User Biasa) ---
            user = request.user
            context = {} 
            
            # Ambil data progres per modul (Kode Anda sebelumnya)
            if Module and UserLessonProgress and Lesson: # Cek jika model ada
                modules = Module.objects.all().order_by('order')
                completed_progress_records = UserLessonProgress.objects.filter(user=user).select_related('lesson__topic__module')
                
                module_progress_data = []
                for module in modules:
                    lesson_ids_in_module = Lesson.objects.filter(topic__module=module).values_list('id', flat=True)
                    total_lessons_in_module = len(lesson_ids_in_module)
                    completed_in_module_count = completed_progress_records.filter(lesson_id__in=lesson_ids_in_module).count()
                    
                    percentage = 0
                    if total_lessons_in_module > 0:
                        percentage = round((completed_in_module_count / total_lessons_in_module) * 100)
                        
                    module_progress_data.append({
                        'module': module, 
                        # Kirim juga slug modul untuk URL di template dashboard
                        'module_url': reverse('learning:module_detail', kwargs={'slug': module.slug}), 
                        'completed': completed_in_module_count,
                        'total': total_lessons_in_module, 
                        'percentage': percentage,
                    })
                context['module_progress_list'] = module_progress_data # Nama ini sesuai template dashboard terakhir
            else:
                 context['module_progress_list'] = None # Kirim None jika model learning tidak ada

            # Render template dashboard user biasa 
            # (Pastikan path template ini benar: 'core/dashboard.html' atau 'dashboard.html')
            return render(request, 'core/dashboard.html', context) 

    else:
        # --- Logika untuk Pengguna Anonim (Homepage Publik) ---
        # Mengambil artikel terbaru (Kode Anda sebelumnya)
        context = {} 
        if Article: # Cek jika model Article ada
            try:
                # Pastikan field 'status' dan konstanta 'Article.Status.PUBLISHED' ada
                # dan field 'created_at' ada untuk ordering
                recent_articles = Article.objects.filter(status=Article.Status.PUBLISHED).order_by('-created_at')[:3]
                context['recent_articles'] = recent_articles 
            except Exception as e:
                # Tangani jika query gagal (misal field tidak ada)
                print(f"Error fetching articles for public index: {e}")
                context['recent_articles'] = None
        else:
             context['recent_articles'] = None # Kirim None jika model Article tidak ada

        # Render template homepage publik 
        # (Pastikan path template ini benar: 'core/index.html' atau 'index.html')
        return render(request, 'core/index.html', context)

# --- Custom Login View (Diperbarui) ---
class CustomLoginView(LoginView):
    """ Login View Kustom untuk menggunakan form kustom dan redirect role """
    template_name = 'registration/login.html' # Pastikan path template login benar
    # === PERBAIKAN: Gunakan form kustom ===
    authentication_form = CustomAuthenticationForm 
    
    redirect_authenticated_user = True # Arahkan user yg sudah login

    def get_success_url(self):
        """ Mengembalikan URL tujuan setelah login berhasil berdasarkan role. """
        user = self.request.user 
        # Cek Role Pengguna (Pastikan atribut 'role' dan Enum/konstanta 'Role.TEACHER' ada)
        try:
             is_teacher = hasattr(user, 'role') and user.role == User.Role.TEACHER
        except AttributeError:
             is_teacher = False
             print("WARNING: Could not check User.Role.TEACHER in LoginView.")

        if is_teacher:
            # Arahkan ke dashboard mentor
            return reverse_lazy('mentor:home') # Pastikan URL name ini benar
        else:
            # Untuk role lain (USER, ADMIN, dll), arahkan ke halaman utama
            return reverse_lazy('core:index') # Pastikan URL name ini benar

# --- View Daftar Mentor (Kode Anda sebelumnya, dengan error handling lebih baik) ---
def mentor_list(request):
    mentors = User.objects.none() # Default queryset kosong
    try:
        # Pastikan atribut 'role' dan Enum/konstanta 'Role.TEACHER' ada
        mentors = User.objects.filter(role=User.Role.TEACHER).order_by('first_name', 'last_name')
    except AttributeError: 
        messages.warning(request, "Fitur daftar mentor belum sepenuhnya aktif.")
        print("ERROR: User model missing 'role' attribute or 'Role.TEACHER' definition for mentor_list view.")
    except Exception as e:
        messages.error(request, "Terjadi kesalahan saat memuat daftar mentor.")
        print(f"ERROR in mentor_list view: {e}")
        
    context = {'mentors': mentors} # Nama konteks 'mentors' sesuai template Anda
    # Pastikan path template ini benar
    return render(request, 'core/mentor_list.html', context)

# --- View Bantuan/FAQ (Kode Anda sebelumnya) ---
def bantuan(request):
     context = {}
     # Pastikan path template ini benar
     return render(request, 'core/bantuan.html', context)

# Catatan: View untuk 'profile' dan 'edit_profile' biasanya ada di accounts/views.py
# Jika memang ada di core/views.py, pastikan logika dan impornya benar.