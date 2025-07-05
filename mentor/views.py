# mentor/views.py
from django.forms import inlineformset_factory
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.urls import reverse
from learning.models import Choice, Lesson, QuizAttempt, UserLessonProgress, Topic, Module, Quiz, Question, PretestAttempt 
from .forms import ChoiceForm, Module, TopicForm, LessonForm, ModuleForm, QuizForm, QuestionForm
from django.contrib.auth import get_user_model

# --- Impor baru yang dibutuhkan untuk Profil Mentor ---
from accounts.decorators import teacher_required
from accounts.forms import ProfileUpdateForm
from accounts.models import MentorApplication
# --- Akhir impor baru ---

import datetime
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncDate

User = get_user_model()

# ======================================================================
# SEMUA VIEW ANDA YANG SUDAH ADA TETAP DI SINI (DARI home_mentor HINGGA user_activity_detail)
# ======================================================================

@login_required
def home_mentor(request):
    """
    Menampilkan halaman dashboard utama untuk Mentor, 
    termasuk ringkasan data dan aktivitas terbaru.
    """
    # Pemeriksaan Role Mentor
    if not hasattr(request.user, 'role') or request.user.role != User.Role.TEACHER:
         raise PermissionDenied("Hanya mentor yang dapat mengakses halaman ini.")

    # --- Ambil Data Aktivitas Terbaru (seperti sebelumnya) ---
    num_recent = 5 # Jumlah item terbaru
    try:
        recent_activity = UserLessonProgress.objects.select_related(
            'user', 'lesson__topic'
        ).order_by('-completed_at')[:num_recent]
    except Exception as e:
        print(f"Error fetching recent progress: {e}")
        recent_activity = []

    try:
        recent_lessons = Lesson.objects.select_related('topic').order_by('-id')[:num_recent]
    except Exception as e:
        print(f"Error fetching recent lessons: {e}")
        recent_lessons = []
        
    # --- TAMBAHAN: Hitung Data untuk Kartu Ringkasan ---
    try:
        student_count = User.objects.filter(role=User.Role.USER).count()
        module_count = Module.objects.count()
        topic_count = Topic.objects.count()
        lesson_count = Lesson.objects.count()
        quiz_count = Quiz.objects.count()
    except Exception as e:
        print(f"Error calculating summary counts for mentor dashboard: {e}")
        student_count = module_count = topic_count = lesson_count = quiz_count = 'N/A' # Tampilkan N/A jika error
    # --- AKHIR TAMBAHAN ---

    # Siapkan context untuk Template
    context = {
        'recent_activity': recent_activity, 
        'recent_materials': recent_lessons,    
        # --- TAMBAHAN: Kirim data counts ke context ---
        'student_count': student_count,
        'module_count': module_count,
        'topic_count': topic_count,
        'lesson_count': lesson_count,
        'quiz_count': quiz_count,
        # --- AKHIR TAMBAHAN ---
    }
    
    return render(request, 'mentor/home_mentor.html', context)

@login_required
def list_modules(request):
    """ Menampilkan daftar semua Modul pembelajaran. """
    # Pemeriksaan Role Mentor
    if not hasattr(request.user, 'role') or request.user.role != User.Role.TEACHER:
         raise PermissionDenied("Hanya mentor yang dapat mengakses halaman ini.")

    # Ambil semua modul, urutkan berdasarkan order dan title
    try:
        all_modules = Module.objects.all().order_by('order', 'title')
    except Exception as e:
        print(f"Error fetching modules: {e}")
        all_modules = []

    context = {
        'modules': all_modules,
    }
    # Render template yang akan kita buat
    return render(request, 'mentor/materi_module_list.html', context)

@login_required
def module_detail_mentor(request, module_slug):
     # Pemeriksaan Role Mentor
    if not hasattr(request.user, 'role') or request.user.role != User.Role.TEACHER:
         raise PermissionDenied("Hanya mentor yang dapat mengakses halaman ini.")
         
    module = get_object_or_404(Module, slug=module_slug)
    topics_in_module = module.topics.order_by('order', 'title') # Ambil topik HANYA dari modul ini

    context = {
        'module': module,
        'topics': topics_in_module
    }
    # Render template yang akan menampilkan daftar topik (akan dibuat / disesuaikan)
    return render(request, 'mentor/module_detail_mentor.html', context)

@login_required
def add_module(request):
    """ Menampilkan form untuk menambah modul baru dan memproses submit form. """
    # Pemeriksaan Role Mentor
    if not hasattr(request.user, 'role') or request.user.role != User.Role.TEACHER:
        raise PermissionDenied("Hanya mentor yang dapat mengakses halaman ini.")

    if request.method == 'POST':
        # Jika method adalah POST, proses data form modul
        form = ModuleForm(request.POST) 
        if form.is_valid():
            # Jika valid, simpan objek Module baru
            new_module = form.save() # Slug akan dibuat otomatis oleh model
            messages.success(request, f"Modul '{new_module.title}' berhasil ditambahkan.")
            # Arahkan kembali ke halaman daftar modul
            return redirect('mentor:materi_module_list')
        else:
            # Jika form tidak valid, tampilkan form lagi dengan error
            messages.error(request, "Terjadi kesalahan. Silakan periksa input form.")
            # Biarkan proses lanjut ke render di bawah
    else:
        # Jika method GET, tampilkan form ModuleForm yang kosong
        form = ModuleForm()

    # Siapkan context untuk dikirim ke template
    context = {
        'form': form,
    }
    # Render template form tambah modul (akan dibuat selanjutnya)
    return render(request, 'mentor/tambah_modul.html', context)

@login_required
def edit_module(request, slug):
    """ Menampilkan form untuk mengedit modul yang ada dan memproses submit form. """
    # Pemeriksaan Role Mentor
    if not hasattr(request.user, 'role') or request.user.role != User.Role.TEACHER:
        raise PermissionDenied("Hanya mentor yang dapat mengakses halaman ini.")

    # Ambil objek Module yang mau diedit berdasarkan slug
    module = get_object_or_404(Module, slug=slug)

    if request.method == 'POST':
        # Jika method POST, proses data pembaruan
        # Berikan instance=module agar form tahu ini adalah update
        form = ModuleForm(request.POST, instance=module) 
        if form.is_valid():
            # Jika valid, simpan perubahan ke objek module yang ada
            updated_module = form.save() 
            # Slug mungkin akan diperbarui otomatis jika title berubah oleh model save()
            messages.success(request, f"Modul '{updated_module.title}' berhasil diperbarui.")
            # Arahkan kembali ke daftar modul
            return redirect('mentor:materi_module_list')
        else:
            messages.error(request, "Terjadi kesalahan. Silakan periksa input form.")
            # Biarkan render di bawah menampilkan form dengan error
    else:
        # Jika method GET, tampilkan form yang sudah diisi data module saat ini
        form = ModuleForm(instance=module) # instance=module mengisi form

    # Siapkan context
    context = {
        'form': form,
        'module': module, # Kirim objek modul ke template
        'is_edit_mode': True # Flag untuk menandai mode edit
    }
    # Gunakan template yang sama dengan tambah modul
    return render(request, 'mentor/tambah_modul.html', context)

@login_required
def delete_module(request, slug):
    """ Menampilkan halaman konfirmasi hapus dan memproses penghapusan modul. """
    # Pemeriksaan Role Mentor
    if not hasattr(request.user, 'role') or request.user.role != User.Role.TEACHER:
        raise PermissionDenied("Hanya mentor yang dapat mengakses halaman ini.")

    # Ambil objek Module yang mau dihapus berdasarkan slug
    module = get_object_or_404(Module, slug=slug)

    if request.method == 'POST':
        # Jika method POST, artinya pengguna mengklik tombol konfirmasi hapus
        module_title = module.title # Simpan judulnya untuk pesan sukses
        module.delete() # Hapus objek dari database
                        # PERHATIAN: Ini akan menghapus semua Topic, Lesson, Quiz, dll 
                        # di dalam modul ini jika relasinya on_delete=CASCADE!
        messages.success(request, f"Modul '{module_title}' dan semua isinya telah berhasil dihapus.")
        # Arahkan kembali ke daftar modul
        return redirect('mentor:materi_module_list')

    # Jika method GET (atau metode lain), tampilkan halaman konfirmasi
    context = {
        'module': module # Kirim objek modul ke template
    }
    # Render template konfirmasi (akan kita buat selanjutnya)
    return render(request, 'mentor/hapus_modul_konfirmasi.html', context)

@login_required
def list_topics(request):
    """ Menampilkan daftar semua Topik yang ada, diurutkan per Modul. """
    # Pemeriksaan Role Mentor (Sama seperti di home_mentor)
    if not hasattr(request.user, 'role') or request.user.role != User.Role.TEACHER:
         raise PermissionDenied("Hanya mentor yang dapat mengakses halaman ini.")

    # Ambil semua topik, urutkan berdasarkan urutan modul, judul modul, lalu urutan topik
    # Gunakan select_related('module') agar efisien saat mengakses nama modul di template
    try:
        all_topics = Topic.objects.select_related('module').order_by(
            'module__order', 'module__title', 'order', 'title'
        )
    except Exception as e:
        print(f"Error fetching topics: {e}")
        all_topics = []

    context = {
        'topics': all_topics,
    }
    # Render template yang akan kita buat selanjutnya
    return render(request, 'mentor/materi_topic_list.html', context)

@login_required
def add_topic(request, module_slug): 
    """ Menampilkan form untuk menambah topik baru ke modul tertentu dan memproses submit. """
    # Pemeriksaan Role Mentor
    if not hasattr(request.user, 'role') or request.user.role != User.Role.TEACHER:
        raise PermissionDenied("Hanya mentor yang dapat mengakses halaman ini.")

    # MODIFIKASI: Ambil objek Module induk berdasarkan slug dari URL
    module = get_object_or_404(Module, slug=module_slug)

    if request.method == 'POST':
        form = TopicForm(request.POST) 
        if form.is_valid():
            # MODIFIKASI: Simpan dengan commit=False dulu
            new_topic = form.save(commit=False) 
            # MODIFIKASI: Set modul induknya
            new_topic.module = module 
            # MODIFIKASI: Baru simpan ke DB
            new_topic.save() 

            messages.success(request, f"Topik '{new_topic.title}' berhasil ditambahkan ke modul '{module.title}'.")
            # MODIFIKASI: Redirect kembali ke halaman detail modul induknya
            return redirect('mentor:module_detail_mentor', module_slug=module.slug) 
        else:
            messages.error(request, "Terjadi kesalahan. Silakan periksa input form.")
    else:
        # MODIFIKASI: Isi field 'module' di form secara otomatis saat GET
        # Ini akan membuat dropdown modul terpilih sesuai modul induk
        form = TopicForm(initial={'module': module}) 

    # Siapkan context, sekarang sertakan juga objek module
    context = {
        'form': form,
        'module': module, # Kirim objek modul ke template
    }
    # Render template yang sama (tambah_topik.html)
    return render(request, 'mentor/tambah_topik.html', context)

@login_required
def edit_topic(request, slug):
    """ Menampilkan form untuk mengedit topik yang ada dan memproses submit form. """
    if not hasattr(request.user, 'role') or request.user.role != User.Role.TEACHER:
        raise PermissionDenied("Hanya mentor yang dapat mengakses halaman ini.")
        
    topic = get_object_or_404(Topic.objects.select_related('module'), slug=slug) # Tambahkan select_related

    if request.method == 'POST':
        form = TopicForm(request.POST, instance=topic) 
        if form.is_valid():
            updated_topic = form.save() 
            messages.success(request, f"Topik '{updated_topic.title}' berhasil diperbarui.")
            # Kembali ke detail modul tempat topik ini berada
            return redirect('mentor:module_detail_mentor', module_slug=updated_topic.module.slug) 
        else:
            messages.error(request, "Terjadi kesalahan. Silakan periksa input form.")
    else:
        form = TopicForm(instance=topic) 

    context = {
        'form': form,
        'topic': topic, # Kirim objek topik ke template
        'module': topic.module, # Kirim juga objek modul induk
        'is_edit_mode': True 
    }
    # Gunakan template tambah_topik.html untuk edit juga
    return render(request, 'mentor/tambah_topik.html', context)

@login_required
def delete_topic(request, slug):
    """ Menampilkan halaman konfirmasi hapus dan memproses penghapusan topik. """
    if not hasattr(request.user, 'role') or request.user.role != User.Role.TEACHER:
        raise PermissionDenied("Hanya mentor yang dapat mengakses halaman ini.")

    topic = get_object_or_404(Topic.objects.select_related('module'), slug=slug) # Tambahkan select_related

    if request.method == 'POST':
        topic_title = topic.title 
        module_slug = topic.module.slug # Simpan slug modul sebelum dihapus
        topic.delete() 
        messages.success(request, f"Topik '{topic_title}' dan semua pelajarannya telah berhasil dihapus.")
        # Kembali ke detail modul tempat topik tadi berada
        return redirect('mentor:module_detail_mentor', module_slug=module_slug) 
    
    context = {
        'topic': topic,
        'module': topic.module # Kirim module untuk link Batal
    }
    return render(request, 'mentor/hapus_topik_konfirmasi.html', context)

@login_required
def topic_detail_mentor(request, slug):
    """ Menampilkan detail sebuah topik, daftar pelajaran, dan daftar kuis di dalamnya untuk Mentor. """
    if not hasattr(request.user, 'role') or request.user.role != User.Role.TEACHER:
         raise PermissionDenied("Hanya mentor yang dapat mengakses halaman ini.")

    topic = get_object_or_404(Topic.objects.select_related('module'), slug=slug)
    lessons = topic.lessons.order_by('order', 'title')

    # --- TAMBAHAN: Ambil Kuis untuk topik ini ---
    # Menggunakan related_name 'quizzes' dari ForeignKey di model Quiz ke Topic
    # Urutkan berdasarkan order atau title
    quizzes = topic.quizzes.order_by('order', 'title') 
    # --- AKHIR TAMBAHAN ---

    context = {
        'topic': topic,    
        'lessons': lessons,  
        'quizzes': quizzes, # <-- Kirim daftar kuis ke template
    }
    return render(request, 'mentor/topic_detail_mentor.html', context)

@login_required
def add_lesson(request, topic_slug):
    """ Menampilkan form untuk menambah pelajaran baru ke topik tertentu dan memproses submit. """
    # Pemeriksaan Role Mentor
    if not hasattr(request.user, 'role') or request.user.role != User.Role.TEACHER:
        raise PermissionDenied("Hanya mentor yang dapat mengakses halaman ini.")

    # Ambil objek Topic induk berdasarkan slug dari URL
    topic = get_object_or_404(Topic, slug=topic_slug)

    if request.method == 'POST':
        # Jika method POST, proses data form pelajaran
        form = LessonForm(request.POST)
        if form.is_valid():
            # Jika valid, JANGAN langsung simpan ke DB (commit=False)
            # karena kita perlu set field 'topic' nya dulu
            new_lesson = form.save(commit=False) 
            # Set topik induk untuk pelajaran baru ini
            new_lesson.topic = topic 
            # Sekarang baru simpan ke database
            new_lesson.save() 
            # Slug pelajaran akan otomatis dibuat oleh model save() Lesson jika ada

            messages.success(request, f"Pelajaran '{new_lesson.title}' berhasil ditambahkan ke topik '{topic.title}'.")
            # Redirect kembali ke halaman detail topik induknya
            return redirect('mentor:topic_detail_mentor', slug=topic.slug)
        else:
            # Jika form tidak valid, tampilkan form lagi dengan error
            messages.error(request, "Terjadi kesalahan. Silakan periksa input form.")
            pass # Lanjut ke render di bawah
    else:
        # Jika method GET, tampilkan form LessonForm yang kosong
        form = LessonForm()

    # Siapkan context, kirim form dan objek topik induk
    context = {
        'form': form,
        'topic': topic, # Kirim objek topik agar template tahu konteksnya
    }
    # Render template form tambah pelajaran (akan dibuat)
    return render(request, 'mentor/tambah_lesson.html', context)

@login_required
def edit_lesson(request, pk): # Terima Primary Key (pk) dari URL
    """ Menampilkan form untuk mengedit pelajaran yang ada dan memproses submit form. """
    # Pemeriksaan Role Mentor
    if not hasattr(request.user, 'role') or request.user.role != User.Role.TEACHER:
        raise PermissionDenied("Hanya mentor yang dapat mengakses halaman ini.")

    # Ambil objek Lesson yang mau diedit berdasarkan pk
    # Sertakan topic agar bisa redirect & tampilkan info di template
    lesson = get_object_or_404(Lesson.objects.select_related('topic'), pk=pk) 
    topic = lesson.topic # Ambil topik induknya

    if request.method == 'POST':
        # Jika method POST, proses data pembaruan
        # Berikan instance=lesson agar form tahu ini adalah update
        form = LessonForm(request.POST, instance=lesson) 
        if form.is_valid():
            # Jika valid, simpan perubahan ke objek lesson yang ada
            updated_lesson = form.save() 
            # Slug pelajaran mungkin perlu diperbarui jika title berubah (jika lesson punya slug)
            messages.success(request, f"Pelajaran '{updated_lesson.title}' berhasil diperbarui.")
            # Arahkan kembali ke halaman detail topik induknya
            return redirect('mentor:topic_detail_mentor', slug=topic.slug) 
        else:
            messages.error(request, "Terjadi kesalahan. Silakan periksa input form.")
            # Biarkan render di bawah menampilkan form dengan error
    else:
        # Jika method GET, tampilkan form yang sudah diisi data lesson saat ini
        form = LessonForm(instance=lesson) # instance=lesson mengisi form

    # Siapkan context
    context = {
        'form': form,
        'lesson': lesson, # Kirim objek lesson yang diedit
        'topic': topic,   # Kirim objek topik induknya
        'is_edit_mode': True # Flag untuk menandai mode edit
    }
    # Gunakan template yang sama dengan tambah pelajaran
    return render(request, 'mentor/tambah_lesson.html', context)

@login_required
def delete_lesson(request, pk): # Terima Primary Key (pk) dari URL
    """ Menampilkan halaman konfirmasi hapus dan memproses penghapusan pelajaran. """
    # Pemeriksaan Role Mentor
    if not hasattr(request.user, 'role') or request.user.role != User.Role.TEACHER:
        raise PermissionDenied("Hanya mentor yang dapat mengakses halaman ini.")

    # Ambil objek Lesson yang mau dihapus berdasarkan pk
    # Sertakan topic agar bisa redirect kembali ke halaman detail topik yang benar
    lesson = get_object_or_404(Lesson.objects.select_related('topic'), pk=pk)
    topic = lesson.topic # Simpan objek topik induknya

    if request.method == 'POST':
        # Jika method POST, pengguna mengklik tombol konfirmasi hapus
        lesson_title = lesson.title # Simpan judulnya untuk pesan sukses
        lesson.delete() # Hapus objek dari database
        messages.success(request, f"Pelajaran '{lesson_title}' telah berhasil dihapus.")
        # Arahkan kembali ke halaman detail topik induknya
        return redirect('mentor:topic_detail_mentor', slug=topic.slug)

    # Jika method GET (atau metode lain), tampilkan halaman konfirmasi
    context = {
        'lesson': lesson, # Kirim objek pelajaran ke template
        'topic': topic    # Kirim juga objek topik induknya
    }
    # Render template konfirmasi (akan kita buat selanjutnya)
    return render(request, 'mentor/hapus_pelajaran_konfirmasi.html', context)

@login_required
def add_quiz(request, topic_slug): # Terima topic_slug dari URL
    """ Menampilkan form untuk menambah kuis baru ke topik tertentu dan memproses submit. """
    # Pemeriksaan Role Mentor
    if not hasattr(request.user, 'role') or request.user.role != User.Role.TEACHER:
        raise PermissionDenied("Hanya mentor yang dapat mengakses halaman ini.")

    # Ambil objek Topic induk berdasarkan slug dari URL
    topic = get_object_or_404(Topic, slug=topic_slug)

    if request.method == 'POST':
        # Jika method POST, proses data form kuis
        form = QuizForm(request.POST)
        if form.is_valid():
            # Jika valid, JANGAN langsung simpan (commit=False)
            new_quiz = form.save(commit=False)
            # Set topik induk untuk kuis baru ini
            new_quiz.topic = topic
            # Sekarang baru simpan ke database
            new_quiz.save()
            # Slug untuk Quiz mungkin tidak otomatis dibuat oleh model Anda,
            # periksa model Quiz jika Anda ingin slug untuk kuis.

            messages.success(request, f"Kuis '{new_quiz.title}' berhasil ditambahkan ke topik '{topic.title}'.")
            # Redirect kembali ke halaman detail topik induknya
            return redirect('mentor:topic_detail_mentor', slug=topic.slug)
        else:
            # Jika form tidak valid, tampilkan form lagi dengan error
            messages.error(request, "Terjadi kesalahan. Silakan periksa input form.")
            # Biarkan proses lanjut ke render di bawah
    else:
        # Jika method GET, tampilkan form QuizForm yang kosong
        form = QuizForm()

    # Siapkan context, kirim form dan objek topik induk
    context = {
        'form': form,
        'topic': topic, # Kirim objek topik agar template tahu konteksnya
    }
    # Render template form tambah kuis (akan dibuat selanjutnya)
    return render(request, 'mentor/tambah_kuis.html', context)

@login_required
def edit_quiz(request, pk): # Terima Primary Key Kuis (pk) dari URL
    """ Menampilkan form untuk mengedit kuis yang ada dan memproses submit form. """
    # Pemeriksaan Role Mentor
    if not hasattr(request.user, 'role') or request.user.role != User.Role.TEACHER:
        raise PermissionDenied("Hanya mentor yang dapat mengakses halaman ini.")

    # Ambil objek Kuis yang mau diedit berdasarkan pk
    # Sertakan topic agar bisa redirect & tampilkan info di template
    quiz = get_object_or_404(Quiz.objects.select_related('topic'), pk=pk)
    topic = quiz.topic # Ambil topik induknya

    if request.method == 'POST':
        # Jika method POST, proses data pembaruan
        # Berikan instance=quiz agar form tahu ini adalah update
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            # Jika valid, simpan perubahan ke objek quiz yang ada
            updated_quiz = form.save()
            messages.success(request, f"Kuis '{updated_quiz.title}' berhasil diperbarui.")
            # Arahkan kembali ke halaman detail topik induknya
            return redirect('mentor:topic_detail_mentor', slug=topic.slug)
        else:
            messages.error(request, "Terjadi kesalahan. Silakan periksa input form.")
            # Biarkan render di bawah menampilkan form dengan error
    else:
        # Jika method GET, tampilkan form yang sudah diisi data kuis saat ini
        form = QuizForm(instance=quiz) # instance=quiz mengisi form

    # Siapkan context
    context = {
        'form': form,
        'quiz': quiz,     # Kirim objek kuis yang diedit
        'topic': topic,   # Kirim objek topik induknya
        'is_edit_mode': True # Flag untuk menandai mode edit
    }
    # Gunakan template yang sama dengan tambah kuis
    return render(request, 'mentor/tambah_kuis.html', context)

@login_required
def delete_quiz(request, pk): # Terima Primary Key Kuis (pk) dari URL
    """ Menampilkan halaman konfirmasi hapus dan memproses penghapusan kuis. """
    # Pemeriksaan Role Mentor
    if not hasattr(request.user, 'role') or request.user.role != User.Role.TEACHER:
        raise PermissionDenied("Hanya mentor yang dapat mengakses halaman ini.")

    # Ambil objek Kuis yang mau dihapus berdasarkan pk
    # Sertakan topic agar bisa redirect kembali & tampilkan info di template
    quiz = get_object_or_404(Quiz.objects.select_related('topic'), pk=pk)
    topic = quiz.topic # Simpan objek topik induknya

    if request.method == 'POST':
        # Jika method POST, pengguna mengklik tombol konfirmasi hapus
        quiz_title = quiz.title # Simpan judulnya untuk pesan sukses
        topic_slug_redirect = topic.slug # Simpan slug topik untuk redirect sebelum kuis dihapus
        
        quiz.delete() # Hapus objek kuis dari database
                      # PERHATIAN: Ini akan menghapus semua Question, Choice, 
                      # dan QuizAttempt terkait jika on_delete=CASCADE!
                      
        messages.success(request, f"Kuis '{quiz_title}' dan semua isinya (pertanyaan, pilihan, upaya) telah berhasil dihapus.")
        # Arahkan kembali ke halaman detail topik induknya
        return redirect('mentor:topic_detail_mentor', slug=topic_slug_redirect)
    
    # Jika method GET (atau metode lain), tampilkan halaman konfirmasi
    context = {
        'quiz': quiz,   # Kirim objek kuis ke template
        'topic': topic  # Kirim juga objek topik induknya
    }
    # Render template konfirmasi (akan kita buat selanjutnya)
    return render(request, 'mentor/hapus_kuis_konfirmasi.html', context)

@login_required
def list_questions(request, quiz_pk):
    """ Menampilkan daftar semua pertanyaan DAN pilihan jawabannya untuk kuis tertentu. """
    if not hasattr(request.user, 'role') or request.user.role != User.Role.TEACHER:
         raise PermissionDenied("Hanya mentor yang dapat mengakses halaman ini.")

    quiz = get_object_or_404(Quiz.objects.select_related('topic__module'), pk=quiz_pk)

    # --- MODIFIKASI: Tambahkan prefetch_related untuk choices ---
    # Asumsi: ForeignKey dari Choice ke Question memiliki related_name='choices'
    # Jika tidak ada related_name, gunakan 'choice_set' (nama default Django)
    try:
        questions = quiz.questions.prefetch_related('choices').order_by('order')
    except AttributeError: 
        try: # Fallback ke default related_name
            questions = quiz.question_set.prefetch_related('choice_set').order_by('order')
            print(f"INFO: Menggunakan default 'question_set' dan 'choice_set' untuk Kuis PK: {quiz_pk}")
        except AttributeError:
            print(f"Error: Tidak bisa menemukan related manager untuk Question/Choice dari Quiz (PK: {quiz.pk}). Periksa related_name.")
            questions = Question.objects.none()
    # --- AKHIR MODIFIKASI ---

    # --- DEBUG Print (Opsional, bisa dihapus nanti) ---
    print(f"DEBUG: Questions for quiz '{quiz.title}': {questions}")
    for q in questions:
         # Cek apakah prefetch bekerja (seharusnya tidak ada query tambahan di sini)
         print(f"  - Question {q.pk}: {q.text}")
         print(f"    Choices: {list(q.choices.all())}") # Akses .all() untuk memicu prefetch
    print("--- END DEBUG ---")
    # --- AKHIR DEBUG Print ---

    context = {
        'quiz': quiz,           
        'questions': questions, # Sekarang questions membawa data choices yang sudah di-prefetch
    }
    return render(request, 'mentor/list_questions.html', context)

@login_required
def add_question(request, quiz_pk): 
    """ Menampilkan form untuk menambah pertanyaan BARU beserta pilihan jawabannya ke kuis tertentu. """
    if not hasattr(request.user, 'role') or request.user.role != User.Role.TEACHER:
        raise PermissionDenied("Hanya mentor yang dapat mengakses halaman ini.")

    quiz = get_object_or_404(Quiz.objects.select_related('topic__module'), pk=quiz_pk)

    # --- BUAT FORMSET UNTUK PILIHAN JAWABAN ---
    # Parameter: ParentModel, ChildModel, form=ChildForm, extra=Jumlah form kosong, can_delete=False (karena ini add)
    ChoiceInlineFormSet = inlineformset_factory(
        Question, # Model Induk (Parent)
        Choice, # Model Anak (Child)
        form=ChoiceForm, # Form yang digunakan untuk setiap item anak
        fields=['text', 'is_correct'], # Field dari Choice yang mau dimasukkan
        extra=4, # Jumlah form pilihan jawaban kosong yang ditampilkan (misal: 4)
        can_delete=False # Tidak perlu opsi delete saat menambah pertanyaan baru
    )
    # --- AKHIR FORMSET ---

    if request.method == 'POST':
        # Buat instance form pertanyaan DAN formset pilihan dengan data POST
        form = QuestionForm(request.POST)
        formset = ChoiceInlineFormSet(request.POST) # Beri data POST ke formset

        # Validasi KEDUA form DAN formset
        if form.is_valid() and formset.is_valid():
            # Simpan pertanyaan dulu (commit=False)
            question = form.save(commit=False)
            question.quiz = quiz # Set kuis induknya
            question.save() # Simpan pertanyaan ke DB untuk mendapatkan ID

            # --- PENTING: Kaitkan formset dengan instance pertanyaan ---
            formset.instance = question 
            # Simpan semua pilihan jawaban di formset (otomatis terhubung ke question)
            formset.save() 

            messages.success(request, f"Pertanyaan '{question.text[:50]}...' dan pilihan jawabannya berhasil ditambahkan ke kuis '{quiz.title}'.")
            # Redirect kembali ke halaman daftar pertanyaan kuis ini
            return redirect('mentor:list_questions', quiz_pk=quiz.pk)
        else:
            # Jika salah satu tidak valid, tampilkan error
            messages.error(request, "Terjadi kesalahan. Silakan periksa input form pertanyaan dan pilihan jawaban.")
    else:
        # Jika GET, buat form pertanyaan kosong dan formset pilihan kosong
        form = QuestionForm()
        # Saat GET, formset tidak perlu instance spesifik question
        formset = ChoiceInlineFormSet() 

    # Kirim form pertanyaan, formset pilihan, dan objek kuis ke template
    context = {
        'form': form,       # Form untuk Question
        'formset': formset, # Formset untuk Choices
        'quiz': quiz,       # Objek Kuis induk
    }
    # Render template yang sama (akan dimodifikasi untuk menampilkan formset)
    return render(request, 'mentor/tambah_question.html', context)

@login_required
def edit_question(request, pk): # Terima Primary Key Pertanyaan (pk) dari URL
    """ Menampilkan form untuk mengedit pertanyaan yang ada beserta pilihan jawabannya. """
    # Pemeriksaan Role Mentor
    if not hasattr(request.user, 'role') or request.user.role != User.Role.TEACHER:
        raise PermissionDenied("Hanya mentor yang dapat mengakses halaman ini.")

    # Ambil objek Question yang mau diedit berdasarkan pk
    # Sertakan quiz dan topic agar bisa redirect & tampilkan info di template
    question = get_object_or_404(Question.objects.select_related('quiz__topic'), pk=pk)
    quiz = question.quiz # Ambil objek kuis induknya

    # --- Definisikan Formset untuk Pilihan Jawaban (Mirip add_question) ---
    # PENTING: Tambahkan can_delete=True dan atur extra=1 (atau 0 jika tidak ingin form kosong tambahan)
    ChoiceInlineFormSet = inlineformset_factory(
        Question, 
        Choice, 
        form=ChoiceForm, 
        fields=['text', 'is_correct'],
        extra=1, # Tampilkan 1 form kosong ekstra untuk menambah pilihan baru dengan mudah
        can_delete=True # Izinkan penghapusan pilihan jawaban yang ada
    )

    if request.method == 'POST':
        # Jika method POST, proses data pembaruan untuk pertanyaan DAN pilihan
        # Berikan instance=question pada kedua form
        form = QuestionForm(request.POST, instance=question)
        formset = ChoiceInlineFormSet(request.POST, instance=question)

        # Validasi keduanya
        if form.is_valid() and formset.is_valid():
            # Simpan perubahan pada pertanyaan
            form.save() 
            # Simpan perubahan pada pilihan jawaban (termasuk penambahan/penghapusan)
            formset.save() 

            messages.success(request, f"Pertanyaan '{question.text[:50]}...' dan pilihan jawabannya berhasil diperbarui.")
            # Redirect kembali ke halaman daftar pertanyaan kuis ini
            return redirect('mentor:list_questions', quiz_pk=quiz.pk)
        else:
            messages.error(request, "Terjadi kesalahan. Silakan periksa input form pertanyaan dan pilihan jawaban.")
            # Biarkan render di bawah menampilkan form dengan error
    else:
        # Jika method GET, tampilkan form pertanyaan & formset pilihan yang sudah diisi data saat ini
        form = QuestionForm(instance=question) # instance=question mengisi form pertanyaan
        formset = ChoiceInlineFormSet(instance=question) # instance=question mengisi formset dengan pilihan yg ada

    # Siapkan context
    context = {
        'form': form,         # Form Pertanyaan
        'formset': formset,   # Formset Pilihan Jawaban
        'quiz': quiz,         # Objek Kuis induk
        'question': question, # Objek Pertanyaan yang diedit
        'is_edit_mode': True  # Flag untuk menandai mode edit di template
    }
    # Gunakan template yang sama dengan tambah pertanyaan
    return render(request, 'mentor/tambah_question.html', context)

@login_required
def delete_question(request, pk): # Terima Primary Key Pertanyaan (pk) dari URL
    """ Menampilkan halaman konfirmasi hapus dan memproses penghapusan pertanyaan. """
    # Pemeriksaan Role Mentor
    if not hasattr(request.user, 'role') or request.user.role != User.Role.TEACHER:
        raise PermissionDenied("Hanya mentor yang dapat mengakses halaman ini.")

    # Ambil objek Question yang mau dihapus berdasarkan pk
    # Sertakan quiz dan topic agar bisa redirect & tampilkan info di template
    question = get_object_or_404(Question.objects.select_related('quiz__topic'), pk=pk)
    quiz = question.quiz # Simpan objek kuis induknya

    if request.method == 'POST':
        # Jika method POST, pengguna mengklik tombol konfirmasi hapus
        question_text = question.text # Simpan teksnya untuk pesan sukses
        quiz_pk_redirect = quiz.pk # Simpan PK kuis untuk redirect sebelum question dihapus
        
        question.delete() # Hapus objek pertanyaan dari database
                          # Ini juga akan menghapus semua Choice terkait jika on_delete=CASCADE
                          
        messages.success(request, f"Pertanyaan '{question_text[:50]}...' telah berhasil dihapus.")
        # Arahkan kembali ke halaman daftar pertanyaan untuk kuis tersebut
        return redirect('mentor:list_questions', quiz_pk=quiz_pk_redirect)
    
    # Jika method GET (atau metode lain), tampilkan halaman konfirmasi
    context = {
        'question': question, # Kirim objek pertanyaan ke template
        'quiz': quiz          # Kirim juga objek kuis induknya
    }
    # Render template konfirmasi (akan kita buat selanjutnya)
    return render(request, 'mentor/hapus_question_konfirmasi.html', context)

@login_required
def analytics_dashboard(request):
    """ 
    Menampilkan halaman analisis untuk Mentor, termasuk ringkasan data 
    dan data aktivitas 7 hari terakhir untuk grafik.
    """
    # Pemeriksaan Role Mentor
    if not hasattr(request.user, 'role') or request.user.role != User.Role.TEACHER:
        raise PermissionDenied("Hanya mentor yang dapat mengakses halaman ini.")

    # === 1. Hitung Data untuk Kartu Ringkasan ===
    try:
        student_count = User.objects.filter(role=User.Role.USER).count()
        module_count = Module.objects.count()
        topic_count = Topic.objects.count()
        lesson_count = Lesson.objects.count()
        quiz_count = Quiz.objects.count()
    except Exception as e:
        print(f"Error calculating summary counts: {e}")
        student_count = module_count = topic_count = lesson_count = quiz_count = 0

    # === 2. Siapkan Data untuk Grafik Aktivitas 7 Hari Terakhir ===
    chart_labels = []
    chart_lessons_data = []
    chart_quizzes_data = []
    
    try:
        # Tentukan rentang tanggal (hari ini dan 6 hari sebelumnya)
        today = timezone.now().date()
        start_date = today - datetime.timedelta(days=6)
        
        # Buat dictionary untuk menampung data per tanggal
        # Kunci: tanggal (str formate-MM-DD), Value: dict {'lessons': count, 'quizzes': count}
        activity_per_day = {
            (start_date + datetime.timedelta(days=i)).strftime('%Y-%m-%d'): {'lessons': 0, 'quizzes': 0} 
            for i in range(7)
        }

        # Query jumlah pelajaran selesai per hari dalam rentang waktu
        lesson_progress_counts = UserLessonProgress.objects.filter(
            completed_at__date__gte=start_date
        ).annotate(
            completion_day=TruncDate('completed_at') # Group by date
        ).values(
            'completion_day' # Pilih kolom tanggal
        ).annotate(
            count=Count('id') # Hitung jumlah record per tanggal
        ).order_by('completion_day') # Urutkan berdasarkan tanggal

        # Masukkan hasil query pelajaran ke dictionary activity_per_day
        for item in lesson_progress_counts:
            date_str = item['completion_day'].strftime('%Y-%m-%d')
            if date_str in activity_per_day: # Pastikan tanggal ada di rentang kita
                activity_per_day[date_str]['lessons'] = item['count']

        # Query jumlah kuis dikerjakan per hari dalam rentang waktu
        quiz_attempt_counts = QuizAttempt.objects.filter(
            completed_at__date__gte=start_date
        ).annotate(
            completion_day=TruncDate('completed_at') # Group by date
        ).values(
            'completion_day' # Pilih kolom tanggal
        ).annotate(
            count=Count('id') # Hitung jumlah record per tanggal
        ).order_by('completion_day') # Urutkan berdasarkan tanggal

        # Masukkan hasil query kuis ke dictionary activity_per_day
        for item in quiz_attempt_counts:
            date_str = item['completion_day'].strftime('%Y-%m-%d')
            if date_str in activity_per_day: # Pastikan tanggal ada di rentang kita
                activity_per_day[date_str]['quizzes'] = item['count']
        
        # Ubah dictionary menjadi list untuk label dan data grafik Chart.js
        chart_labels = list(activity_per_day.keys()) # List tanggal ['2025-04-08', ...]
        chart_lessons_data = [d['lessons'] for d in activity_per_day.values()] # List jumlah pelajaran [0, 2, 1, ...]
        chart_quizzes_data = [d['quizzes'] for d in activity_per_day.values()] # List jumlah kuis [1, 0, 3, ...]

    except Exception as e:
        print(f"Error preparing chart data: {e}")
        # Biarkan list chart kosong jika error

    # === 3. Ambil Daftar Siswa (masih diperlukan jika ingin ditampilkan juga) ===
    try:
        student_users = User.objects.filter(role=User.Role.USER).order_by('username')
    except Exception as e:
        print(f"Error fetching student users: {e}")
        student_users = User.objects.none() 

    # === Siapkan Context untuk Template ===
    context = {
        # Data untuk kartu ringkasan
        'student_count': student_count,
        'module_count': module_count,
        'topic_count': topic_count,
        'lesson_count': lesson_count,
        'quiz_count': quiz_count,
        
        # Data untuk grafik
        'chart_labels': chart_labels,
        'chart_lessons_data': chart_lessons_data,
        'chart_quizzes_data': chart_quizzes_data,

        # Data daftar siswa (jika masih ingin ditampilkan di bawah grafik)
        'students': student_users, 
    }
    
    return render(request, 'mentor/analytics_dashboard.html', context)

@login_required
def user_activity_detail(request, user_pk): # Terima Primary Key User (user_pk) dari URL
    """ Menampilkan detail aktivitas (progres pelajaran & upaya kuis) untuk pengguna tertentu. """
    # Pemeriksaan Role Mentor (yang mengakses)
    if not hasattr(request.user, 'role') or request.user.role != User.Role.TEACHER:
        raise PermissionDenied("Hanya mentor yang dapat mengakses halaman ini.")

    # Ambil objek User (siswa) yang aktivitasnya ingin dilihat
    # Pastikan hanya mengambil user dengan role USER untuk analisis
    student = get_object_or_404(User, pk=user_pk)
    if student.role != User.Role.USER:
        # Sebaiknya tidak menampilkan analisis untuk admin atau mentor lain
        raise Http404("Analisis hanya tersedia untuk pengguna dengan role USER.") 

    # --- Ambil Data Aktivitas untuk Pengguna Spesifik Ini ---
    try:
        # 1. Ambil SEMUA Progres Pelajaran pengguna ini
        progress_records = UserLessonProgress.objects.filter(
            user=student # Filter berdasarkan pengguna yang dipilih
        ).select_related(
            'lesson__topic__module' # Ambil data terkait untuk ditampilkan
        ).order_by('-completed_at') # Urutkan terbaru dulu
    except Exception as e:
        print(f"Error fetching progress records for user {student.username}: {e}")
        progress_records = []

    try:
        # 2. Ambil SEMUA Upaya Kuis pengguna ini
        quiz_attempts = QuizAttempt.objects.filter(
            user=student # Filter berdasarkan pengguna yang dipilih
        ).select_related(
            'quiz__topic__module' # Ambil data terkait untuk ditampilkan
        ).order_by('-completed_at') # Urutkan terbaru dulu
    except Exception as e:
        print(f"Error fetching quiz attempts for user {student.username}: {e}")
        quiz_attempts = []

    pretest_attempts = PretestAttempt.objects.filter(
        user=student
    ).select_related('quiz__topic__module').order_by('-completed_at')

    context = {
        'student': student,               # Objek pengguna yang sedang dianalisis
        'progress_records': progress_records, # Semua progres pelajarannya
        'quiz_attempts': quiz_attempts,  
        'pretest_attempts': pretest_attempts,  
    }
    
    # Render template detail aktivitas pengguna (akan kita buat)
    return render(request, 'mentor/user_activity_detail.html', context)

@login_required
@teacher_required
def mentor_profile(request):
    """Menampilkan halaman profil lengkap seorang mentor."""
    try:
        # Ambil data lamaran yang terhubung dengan mentor yang sedang login
        application_data = request.user.mentor_application
    except MentorApplication.DoesNotExist:
        application_data = None # Handle jika data lamaran tidak ada

    context = {
        'user': request.user,
        'application': application_data,
    }
    return render(request, 'mentor/mentor_profile.html', context)

@login_required
@teacher_required
def edit_mentor_profile(request):
    """Menampilkan dan memproses form untuk edit profil mentor."""
    if request.method == 'POST':
        # Kita gunakan ProfileUpdateForm yang sudah ada
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil Anda berhasil diperbarui.')
            return redirect('mentor:profile') # Kembali ke halaman profil mentor
        else:
            messages.error(request, 'Terjadi kesalahan. Silakan periksa input Anda.')
    else:
        form = ProfileUpdateForm(instance=request.user)

    context = {
        'form': form
    }
    return render(request, 'mentor/edit_mentor_profile.html', context)