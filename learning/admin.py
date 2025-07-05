# learning/admin.py
from django.contrib import admin
from .models import Module, Topic, Lesson, UserLessonProgress
from .models import Module, Topic, Lesson, UserLessonProgress, Quiz, Question, Choice, QuizAttempt, PretestAttempt

# --- Konfigurasi Inline untuk Lesson (agar bisa diedit di halaman Topic) ---
class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1 # Jumlah form kosong Lesson
    prepopulated_fields = {'slug': ('title',)}

# --- Konfigurasi Admin untuk Topic ---
@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'order')
    list_filter = ('module',)
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [LessonInline] # Tampilkan form Lesson di halaman edit Topic

# --- Konfigurasi Inline untuk Topic (agar bisa diedit di halaman Module) ---
class TopicInline(admin.TabularInline):
    model = Topic
    extra = 1
    prepopulated_fields = {'slug': ('title',)}

# --- Konfigurasi Admin untuk Module ---
@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'order')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [TopicInline] # Tampilkan form Topic di halaman edit Module

# --- Konfigurasi Admin untuk UserLessonProgress ---
@admin.register(UserLessonProgress)
class UserLessonProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_lesson_title', 'completed_at')
    list_filter = ('user', 'lesson__topic__module')
    search_fields = ('user__username', 'lesson__title')
    date_hierarchy = 'completed_at'
    readonly_fields = ('completed_at',)

    @admin.display(description='Pelajaran', ordering='lesson__title')
    def get_lesson_title(self, obj):
        # Mengambil judul lesson agar bisa diurutkan di admin
        return obj.lesson.title
    
class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 1 # Tampilkan slot untuk 1 pilihan baru secara default
    # Tambahkan validasi nanti untuk pastikan hanya 1 is_correct per Question

# Admin untuk Question (menyertakan ChoiceInline)
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'order')
    list_filter = ('quiz__topic__module', 'quiz') # Filter berdasarkan modul atau kuis
    search_fields = ('text',)
    inlines = [ChoiceInline] # Tampilkan form Choice di halaman edit Question

# Inline untuk Question (ditampilkan di halaman Quiz)
class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1 # Tampilkan slot untuk 1 pertanyaan baru
    show_change_link = True # Tambahkan link untuk edit detail Question

# Admin untuk Quiz (menyertakan QuestionInline)
@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'topic', 'order', 'pass_mark')
    list_filter = ('topic__module', 'topic') # Filter berdasarkan modul atau topik
    search_fields = ('title', 'description')
    inlines = [QuestionInline] # Tampilkan form Question di halaman edit Quiz
    # prepopulated_fields = {'slug': ('title',)} # Aktifkan jika Anda pakai slug di model Quiz

# Admin untuk QuizAttempt (biasanya read-only di admin)
@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'score', 'passed', 'completed_at')
    list_filter = ('user', 'quiz', 'passed')
    search_fields = ('user__username', 'quiz__title')
    date_hierarchy = 'completed_at'
    # Buat semua field read-only di admin, karena data ini hasil dari pengerjaan kuis
    readonly_fields = ('user', 'quiz', 'score', 'passed', 'completed_at')

    # Kita bisa override agar tidak bisa menambah QuizAttempt dari admin
    def has_add_permission(self, request):
        return False
    # Kita bisa override agar tidak bisa mengubah QuizAttempt dari admin
    def has_change_permission(self, request, obj=None):
        return False

@admin.register(PretestAttempt)
class PretestAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'score', 'passed', 'completed_at')
    list_filter = ('user', 'quiz', 'passed')
    search_fields = ('user__username', 'quiz__title')
    date_hierarchy = 'completed_at'
    
    # Buat semua field read-only, karena ini adalah data historis
    readonly_fields = ('user', 'quiz', 'score', 'passed', 'completed_at')

    # Cegah penambahan atau perubahan data pre-test dari admin secara langsung
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False