# learning/views.py
import time
from .models import Module, Topic, Lesson, UserLessonProgress, Quiz, Question, Choice, QuizAttempt
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin # Untuk Class-Based View
from django.contrib.auth.decorators import login_required # Untuk Function-Based View
from django.views.decorators.http import require_POST # Hanya izinkan POST untuk aksi
from django.contrib import messages
from django.http import Http404, HttpResponse 
from .models import PretestAttempt
from .models import Module, Topic, Lesson, UserLessonProgress
from django.db.models import Max

# --- View Daftar Modul ---
class ModuleListView(ListView):
    model = Module
    template_name = 'learning/module_list.html'
    context_object_name = 'modules'
    # Ordering diambil dari Meta model

# --- View Detail Modul ---
class ModuleDetailView(LoginRequiredMixin, DetailView):
    model = Module
    template_name = 'learning/module_detail.html'
    context_object_name = 'module'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        module = self.get_object()
        user = self.request.user

        # 1. Ambil semua data progres sekali saja untuk efisiensi
        completed_lesson_ids = set(UserLessonProgress.objects.filter(user=user, lesson__topic__module=module).values_list('lesson_id', flat=True))
        passed_quiz_ids = set(QuizAttempt.objects.filter(user=user, quiz__topic__module=module, passed=True).values_list('quiz_id', flat=True))
        attempted_pretest_ids = set(PretestAttempt.objects.filter(user=user, quiz__topic__module=module).values_list('quiz_id', flat=True))

        topics_data = []
        # Flag untuk menentukan apakah topik saat ini bisa diakses, dimulai dari True untuk topik pertama
        can_access_current_topic = True 
        
        all_topics = module.topics.select_related('pretest').prefetch_related('lessons', 'quizzes').all().order_by('order')

        for i, topic in enumerate(all_topics):
            # 2. Cek apakah pre-test (jika ada) sudah diambil
            pretest_is_taken = True # Asumsi default sudah diambil jika tidak ada pre-test
            if topic.pretest:
                if topic.pretest.id not in attempted_pretest_ids:
                    pretest_is_taken = False
            
            # Tentukan apakah topik saat ini dapat diakses
            is_topic_accessible = can_access_current_topic
            
            # 3. Siapkan data pelajaran HANYA JIKA topik dapat diakses dan pre-test sudah diambil
            lessons_status = []
            all_lessons_completed = False
            
            if is_topic_accessible and pretest_is_taken:
                lessons_in_topic = topic.lessons.all().order_by('order')
                completed_lessons_count = 0
                previous_lesson_completed = True # Pelajaran pertama selalu bisa diakses dalam topik yang terbuka

                for lesson in lessons_in_topic:
                    is_completed = lesson.id in completed_lesson_ids
                    is_lesson_accessible = previous_lesson_completed
                    
                    if is_completed:
                        completed_lessons_count += 1
                    
                    lessons_status.append({
                        'lesson': lesson,
                        'is_accessible': is_lesson_accessible,
                        'is_completed': is_completed,
                    })
                    
                    # Untuk iterasi selanjutnya, pelajaran berikutnya hanya bisa diakses jika yang ini selesai
                    previous_lesson_completed = is_completed
                
                if lessons_in_topic.exists() and completed_lessons_count == lessons_in_topic.count():
                    all_lessons_completed = True

            # 4. Tentukan akses untuk TOPIK BERIKUTNYA
            post_test = topic.quizzes.filter(is_pretest=False).first()
            if all_lessons_completed and (not post_test or post_test.id in passed_quiz_ids):
                # Jika semua pelajaran selesai DAN (tidak ada post-test ATAU post-test sudah lulus)
                can_access_current_topic = True
            else:
                # Jika tidak, kunci topik berikutnya
                can_access_current_topic = False

            topics_data.append({
                'topic': topic,
                'lessons_status': lessons_status,
                'quiz': post_test,
                'is_topic_accessible': is_topic_accessible,
                'pretest_taken': pretest_is_taken,
                'all_lessons_completed': all_lessons_completed,
            })
        
        context['topics_data'] = topics_data
        context['passed_quiz_ids'] = passed_quiz_ids # Tetap kirim ini untuk cek status post-test
        return context

# --- View Detail Pelajaran ---
class LessonDetailView(LoginRequiredMixin, DetailView):
    model = Lesson
    template_name = 'learning/lesson_detail.html'
    context_object_name = 'lesson'

    def get_queryset(self):
        # Pastikan hanya lesson dari modul/topic yg published yg bisa diakses (jika ada status publish di modul/topic)
        # Atau cukup filter berdasarkan slug saja jika slug unik global dan tidak ada status publish
        return Lesson.objects.all() # Asumsi semua lesson bisa diakses jika modul/topicnya bisa

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lesson = self.get_object()
        user = self.request.user

        # Cek status selesai
        context['is_completed'] = UserLessonProgress.objects.filter(user=user, lesson=lesson).exists()

        # Cari pelajaran sebelumnya
        try:
            previous_lesson = Lesson.objects.filter(
                topic=lesson.topic, order__lt=lesson.order
            ).order_by('-order').first()
        except Lesson.DoesNotExist:
             previous_lesson = None

        # Cek akses berdasarkan pelajaran sebelumnya
        can_access = False
        if previous_lesson is None: # Pelajaran pertama
            can_access = True
        else: # Ada pelajaran sebelumnya
            if UserLessonProgress.objects.filter(user=user, lesson=previous_lesson).exists():
                can_access = True # Bisa akses jika sebelumnya selesai
        context['can_access'] = can_access

        # Cari pelajaran berikutnya
        try:
            next_lesson = Lesson.objects.filter(
                topic=lesson.topic, order__gt=lesson.order
            ).order_by('order').first()
        except Lesson.DoesNotExist:
            next_lesson = None
        context['next_lesson'] = next_lesson

        return context

# --- View untuk Menandai Pelajaran Selesai ---
@login_required    # Memerlukan login
@require_POST      
def mark_lesson_complete(request, lesson_slug):
    """ Menandai sebuah lesson sebagai selesai untuk user saat ini """
    lesson = get_object_or_404(Lesson, slug=lesson_slug)
    progress, created = UserLessonProgress.objects.get_or_create(
        user=request.user,
        lesson=lesson
    )
    if created:
        messages.success(request, f"Pelajaran '{lesson.title}' ditandai selesai!")
    # else:
        # messages.info(request, f"Pelajaran '{lesson.title}' sudah pernah diselesaikan.")

    # Redirect ke detail modul tempat pelajaran itu berada
    return redirect('learning:module_detail', slug=lesson.topic.module.slug)


@login_required # Pastikan view ini juga memerlukan login
def take_quiz(request, module_slug, topic_slug):
    """ Menampilkan form kuis (GET) dan memproses jawaban (POST) """
    topic = get_object_or_404(Topic, slug=topic_slug, module__slug=module_slug)
    # Asumsi hanya ada satu kuis per topik untuk saat ini
    quiz = get_object_or_404(Quiz, topic=topic)
    questions = quiz.questions.all().order_by('order').prefetch_related('choices')

    if request.method == 'POST':
        # --- Logika Pemrosesan Jawaban ---
        correct_answers = 0
        total_questions = questions.count()

        for question in questions:
            # Dapatkan ID pilihan jawaban yang dikirim dari form
            # Nama input radio adalah 'question_IDPERTANYAAN'
            selected_choice_id = request.POST.get(f'question_{question.pk}')

            if selected_choice_id: # Jika pengguna menjawab pertanyaan ini
                try:
                    # Dapatkan objek Choice berdasarkan ID yang dipilih
                    selected_choice = Choice.objects.get(pk=selected_choice_id)
                    # Pastikan pilihan itu memang milik pertanyaan ini (keamanan)
                    if selected_choice.question == question:
                        if selected_choice.is_correct:
                            correct_answers += 1
                except Choice.DoesNotExist:
                    # Pengguna mengirim ID pilihan yang tidak valid, abaikan saja
                    messages.warning(request, f"Pilihan jawaban tidak valid untuk pertanyaan: {question.text[:50]}...")
                    pass # Lanjut ke pertanyaan berikutnya

        # Hitung skor (persentase)
        score = 0.0
        if total_questions > 0:
            score = round((correct_answers / total_questions) * 100, 2) # Bulatkan 2 desimal

        # Tentukan apakah lulus berdasarkan pass_mark kuis
        passed = score >= quiz.pass_mark

        # Simpan hasil percobaan kuis
        attempt = QuizAttempt.objects.create(
            user=request.user,
            quiz=quiz,
            score=score,
            passed=passed
        )

        # Arahkan ke halaman hasil kuis, kirim ID attempt
        return redirect('learning:quiz_result', attempt_id=attempt.pk)
        # --- Akhir Logika Pemrosesan Jawaban ---

    else: # request.method == 'GET'
        # Tampilkan form kuis seperti sebelumnya
        context = {
            'quiz': quiz,
            'questions': questions,
            'topic': topic, # Kirim topic juga jika perlu untuk breadcrumb/info
            'module': topic.module, # Kirim module juga jika perlu
        }
        return render(request, 'learning/take_quiz.html', context)

@login_required
def quiz_result(request, attempt_id):
    """ Menampilkan hasil pengerjaan kuis """
    # Ambil objek attempt, pastikan milik user yg login, atau 404
    attempt = get_object_or_404(QuizAttempt, pk=attempt_id, user=request.user)

    pretest_attempt = None
    topic = attempt.quiz.topic
    if topic.pretest:
        # Ambil percobaan pre-test terbaru untuk kuis ini oleh user ini
        pretest_attempt = PretestAttempt.objects.filter(
            user=request.user, quiz=topic.pretest
        ).order_by('-completed_at').first()

    context = {
        'attempt': attempt,
        'pretest_attempt': pretest_attempt,
    }
    return render(request, 'learning/quiz_result.html', context)

@login_required
def quiz_history(request, quiz_pk):
    """ Menampilkan semua riwayat pengerjaan post-test (kuis) dan perbandingannya. """
    quiz = get_object_or_404(Quiz, pk=quiz_pk, is_pretest=False)

    # Ambil semua percobaan post-test untuk user ini dan kuis ini
    attempts = QuizAttempt.objects.filter(user=request.user, quiz=quiz).order_by('-completed_at')

    # Cari hasil pre-test terkait
    pretest_attempt = None
    if quiz.topic.pretest:
        pretest_attempt = PretestAttempt.objects.filter(
            user=request.user, quiz=quiz.topic.pretest
        ).order_by('-completed_at').first()

    # Cari skor post-test tertinggi
    best_attempt = attempts.aggregate(Max('score'))['score__max']

    context = {
        'quiz': quiz,
        'attempts': attempts,
        'pretest_attempt': pretest_attempt,
        'best_posttest_score': best_attempt,
    }
    return render(request, 'learning/quiz_history.html', context)

@login_required
def take_pretest(request, topic_slug):
    """ Menampilkan form pre-test (GET) dan memproses jawaban (POST) """
    topic = get_object_or_404(Topic.objects.select_related('module'), slug=topic_slug)
    
    if not topic.pretest:
        raise Http404("Topik ini tidak memiliki pre-test.")

    quiz = topic.pretest
    questions = quiz.questions.all().order_by('order').prefetch_related('choices')

    if request.method == 'POST':
        
        # --- LOGIKA PENCEGAH DUPLIKAT DIMULAI DI SINI ---
        last_submission = request.session.get('last_pretest_submission', 0)
        current_time = time.time()

        # Jika pengiriman terakhir kurang dari 3 detik yang lalu, abaikan permintaan ini
        if current_time - last_submission < 3:
            # Cukup arahkan kembali ke halaman modul seolah-olah tidak terjadi apa-apa
            return redirect('learning:module_detail', slug=topic.module.slug)
        
        # Jika bukan duplikat, catat waktu pengiriman saat ini di sesi
        request.session['last_pretest_submission'] = current_time
        # --- AKHIR LOGIKA PENCEGAH DUPLIKAT ---

        # Logika pemrosesan jawaban (tetap sama)
        correct_answers = 0
        total_questions = questions.count()
        for question in questions:
            selected_choice_id = request.POST.get(f'question_{question.pk}')
            if selected_choice_id:
                try:
                    selected_choice = Choice.objects.get(pk=selected_choice_id)
                    if selected_choice.question == question and selected_choice.is_correct:
                        correct_answers += 1
                except Choice.DoesNotExist:
                    pass

        score = round((correct_answers / total_questions) * 100, 2) if total_questions > 0 else 0.0
        passed = score >= quiz.pass_mark

        # Simpan ke PretestAttempt
        attempt = PretestAttempt.objects.create(
            user=request.user, quiz=quiz, score=score, passed=passed
        )

        # Arahkan ke halaman hasil pre-test
        return redirect('learning:pretest_result', attempt_id=attempt.pk)

    # Logika untuk method GET (tetap sama)
    context = {
        'quiz': quiz,
        'questions': questions,
        'topic': topic,
        'module': topic.module,
        'is_pretest': True,
    }
    return render(request, 'learning/take_quiz.html', context)

@login_required
def pretest_result(request, attempt_id):
    """ Menampilkan hasil pengerjaan pre-test """
    attempt = get_object_or_404(PretestAttempt, pk=attempt_id, user=request.user)
    context = {
        'attempt': attempt
    }
    return render(request, 'learning/pretest_result.html', context)

@login_required
def pretest_history(request, topic_slug):
    """ Menampilkan semua riwayat pengerjaan pre-test untuk sebuah topik. """
    topic = get_object_or_404(Topic, slug=topic_slug)
    if not topic.pretest:
        raise Http404("Topik ini tidak memiliki pre-test.")

    # Ambil semua percobaan pre-test untuk user ini dan pre-test ini
    attempts = PretestAttempt.objects.filter(
        user=request.user, quiz=topic.pretest
    ).order_by('-completed_at')

    context = {
        'topic': topic,
        'quiz': topic.pretest,
        'attempts': attempts
    }
    return render(request, 'learning/pretest_history.html', context)