# learning/models.py
from django.db import models
from django.conf import settings # Untuk merujuk ke model User kustom
from django.utils.text import slugify # Untuk membuat slug URL
from django.utils import timezone # Untuk zona waktu
from django.urls import reverse # Digunakan nanti untuk URL
from django.core.validators import MinValueValidator, MaxValueValidator
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField

# --- Model Module ---
class Module(models.Model):
    """ Modul Pembelajaran (Contoh: HTML Dasar) """
    title = models.CharField(max_length=150, unique=True, verbose_name="Judul Modul")
    slug = models.SlugField(max_length=170, unique=True, blank=True, verbose_name="Slug (untuk URL)")
    description = models.TextField(blank=True, null=True, verbose_name="Deskripsi Singkat")
    order = models.PositiveIntegerField(default=0, verbose_name="Urutan")

    class Meta:
        ordering = ['order', 'title']
        verbose_name = "Modul"
        verbose_name_plural = "Modul"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    # def get_absolute_url(self):
    #     return reverse('learning:module_detail', kwargs={'slug': self.slug})

# --- Model Topic ---
class Topic(models.Model):
    """ Topik di dalam sebuah Modul (Contoh: Tag Dasar HTML) """
    module = models.ForeignKey(
        Module,
        related_name='topics',
        on_delete=models.CASCADE,
        verbose_name="Modul Induk"
    )
    title = models.CharField(max_length=150, verbose_name="Judul Topik")
    slug = models.SlugField(max_length=170, unique=True, blank=True, verbose_name="Slug (untuk URL)") # Buat unik global saja dulu
    description = models.TextField(blank=True, null=True, verbose_name="Deskripsi Singkat")
    order = models.PositiveIntegerField(default=0, verbose_name="Urutan")

    pretest = models.ForeignKey(
        'Quiz', # Merujuk ke model Quiz
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pretest_for_topic',
        verbose_name="Pre-test untuk Topik Ini",
        help_text="Pilih kuis yang akan dijadikan pre-test untuk topik ini."
    )

    class Meta:
        ordering = ['module', 'order', 'title']
        # unique_together = ['module', 'slug'] # Komentari/hapus jika slug unik global
        verbose_name = "Topik"
        verbose_name_plural = "Topik"

    def __str__(self):
        return f"{self.module.title} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    
# --- Model Lesson ---
class Lesson(models.Model):
    """ Pelajaran/Konten di dalam sebuah Topik (Contoh: Penjelasan Tag Paragraf) """
    topic = models.ForeignKey(
        Topic,
        related_name='lessons',
        on_delete=models.CASCADE,
        verbose_name="Topik Induk"
    )
    title = models.CharField(max_length=150, verbose_name="Judul Pelajaran")
    slug = models.SlugField(max_length=170, unique=True, blank=True, verbose_name="Slug (untuk URL)") # Buat unik global saja dulu
    content = RichTextUploadingField(verbose_name="Isi Konten Pelajaran")
    order = models.PositiveIntegerField(default=0, verbose_name="Urutan")

    minimum_reading_time = models.PositiveIntegerField(
        default=5, 
        verbose_name="Waktu Belajar Minimum (Menit)",
        help_text="Tentukan waktu minimum dalam menit yang dibutuhkan untuk mempelajari pelajaran ini."
    )

    class Meta:
        ordering = ['topic', 'order', 'title']
        # unique_together = ['topic', 'slug'] # Komentari/hapus jika slug unik global
        verbose_name = "Pelajaran"
        verbose_name_plural = "Pelajaran"

    def __str__(self):
        return f"{self.topic.title} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    
# --- Model UserLessonProgress ---
class UserLessonProgress(models.Model):
    """ Mencatat pelajaran (lesson) mana yg sudah diselesaikan oleh pengguna (user) """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lesson_progress',
        verbose_name="Pengguna"
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='progress_records',
        verbose_name="Pelajaran"
    )
    completed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Waktu Selesai"
    )

    class Meta:
        unique_together = ['user', 'lesson'] # User hanya bisa selesaikan lesson 1x
        ordering = ['user', '-completed_at']
        verbose_name = "Progres Pelajaran Pengguna"
        verbose_name_plural = "Progres Pelajaran Pengguna"

    def __str__(self):
        return f"{self.user.username} - Menyelesaikan: {self.lesson.title}"
    

class Quiz(models.Model):
    """ Merepresentasikan satu set kuis, terkait dengan sebuah Topik """
    topic = models.ForeignKey(
        Topic,
        related_name='quizzes',    # Dari Topic bisa akses topic.quizzes.all()
        on_delete=models.CASCADE, # Jika Topik dihapus, Kuis ikut terhapus
        verbose_name="Topik Terkait"
    )
    title = models.CharField(max_length=200, verbose_name="Judul Kuis")
    description = models.TextField(blank=True, null=True, verbose_name="Deskripsi Kuis")
    order = models.PositiveIntegerField(default=0, verbose_name="Urutan Kuis dalam Topik")
    pass_mark = models.PositiveSmallIntegerField(
        default=80, # Misalnya, nilai default lulus adalah 80%
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Nilai Lulus (%)",
        help_text="Nilai minimal (persen) untuk lulus kuis."
    )
    time_limit_minutes = models.PositiveIntegerField(
        default=15, 
        verbose_name="Batas Waktu (Menit)",
        help_text="Batas waktu pengerjaan kuis dalam satuan menit."
    )
    
    is_pretest = models.BooleanField(
        default=False,
        verbose_name="Jadikan Kuis ini sebagai Pre-test?",
        help_text="Centang jika kuis ini dapat digunakan sebagai pre-test untuk sebuah modul."
    )

    class Meta:
        ordering = ['topic', 'order', 'title']
        verbose_name = "Kuis"
        verbose_name_plural = "Kuis"
        # unique_together = ['topic', 'slug'] # Jika menggunakan slug

    def __str__(self):
        return f"{self.topic.title} - {self.title}"

    # def save(self, *args, **kwargs): # Jika menggunakan slug
    #     if not self.slug:
    #         self.slug = slugify(f"{self.topic.title}-{self.title}")
    #     super().save(*args, **kwargs)


# --- Model Question ---
class Question(models.Model):
    """ Merepresentasikan satu pertanyaan di dalam sebuah Kuis """
    quiz = models.ForeignKey(
        Quiz,
        related_name='questions', # quiz.questions.all()
        on_delete=models.CASCADE, # Jika Kuis dihapus, Pertanyaan ikut terhapus
        verbose_name="Kuis Terkait"
    )
    text = models.TextField(verbose_name="Teks Pertanyaan")
    order = models.PositiveIntegerField(default=0, verbose_name="Urutan Pertanyaan dalam Kuis")
    # Nanti bisa ditambahkan tipe pertanyaan (pilihan ganda, isian, dll)

    class Meta:
        ordering = ['quiz', 'order']
        verbose_name = "Pertanyaan"
        verbose_name_plural = "Pertanyaan"

    def __str__(self):
        # Tampilkan potongan teks pertanyaan
        return f"{self.quiz.title} - Q{self.order}: {self.text[:50]}..."


# --- Model Choice ---
class Choice(models.Model):
    """ Merepresentasikan satu pilihan jawaban untuk sebuah Pertanyaan (pilihan ganda) """
    question = models.ForeignKey(
        Question,
        related_name='choices',   # question.choices.all()
        on_delete=models.CASCADE, # Jika Pertanyaan dihapus, Pilihan ikut terhapus
        verbose_name="Pertanyaan Terkait"
    )
    text = models.CharField(max_length=500, verbose_name="Teks Pilihan Jawaban")
    is_correct = models.BooleanField(default=False, verbose_name="Apakah Jawaban Benar?")

    class Meta:
        ordering = ['question', 'id'] # Urutkan berdasarkan pertanyaan, lalu ID
        verbose_name = "Pilihan Jawaban"
        verbose_name_plural = "Pilihan Jawaban"

    def __str__(self):
        return f"{self.question.text[:30]}... -> {self.text}"


# --- Model QuizAttempt ---
class QuizAttempt(models.Model):
    """ Mencatat upaya pengguna mengerjakan sebuah Kuis """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='quiz_attempts', # user.quiz_attempts.all()
        on_delete=models.CASCADE,     # Jika User dihapus, usahanya ikut hilang
        verbose_name="Pengguna"
    )
    quiz = models.ForeignKey(
        Quiz,
        related_name='attempts',      # quiz.attempts.all()
        on_delete=models.CASCADE,     # Jika Kuis dihapus, usaha ikut hilang
        verbose_name="Kuis"
    )
    score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        verbose_name="Skor (%)"
    )
    passed = models.BooleanField(default=False, verbose_name="Lulus?")
    completed_at = models.DateTimeField(auto_now_add=True, verbose_name="Waktu Selesai")

    class Meta:
        ordering = ['user', 'quiz', '-completed_at'] # Urutkan per user, per kuis, terbaru dulu
        verbose_name = "Upaya Kuis Pengguna"
        verbose_name_plural = "Upaya Kuis Pengguna"

    def __str__(self):
        status = "Lulus" if self.passed else "Gagal"
        return f"{self.user.username} - {self.quiz.title} ({self.score}%, {status})"

class PretestAttempt(models.Model):
    """ Mencatat upaya pengguna mengerjakan sebuah Pre-test (yang merupakan sebuah Quiz) """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='pretest_attempts',
        on_delete=models.CASCADE,
        verbose_name="Pengguna"
    )
    quiz = models.ForeignKey(
        Quiz,
        related_name='pretest_attempts_records',
        on_delete=models.CASCADE,
        verbose_name="Kuis (Pre-test)"
    )
    score = models.FloatField(default=0.0, verbose_name="Skor (%)")
    passed = models.BooleanField(default=False, verbose_name="Lulus?")
    completed_at = models.DateTimeField(auto_now_add=True, verbose_name="Waktu Selesai")

    class Meta:
        ordering = ['user', 'quiz', '-completed_at']
        verbose_name = "Upaya Pre-test Pengguna"
        verbose_name_plural = "Upaya Pre-test Pengguna"

    def __str__(self):
        status = "Lulus" if self.passed else "Gagal"
        return f"Pre-test: {self.user.username} - {self.quiz.title} ({self.score}%, {status})"