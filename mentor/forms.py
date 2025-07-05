# mentor/forms.py
from django import forms
from learning.models import Topic, Lesson, Module, Quiz, Question, Choice
from ckeditor.widgets import CKEditorWidget

class TopicForm(forms.ModelForm):
    """
    Form Django untuk membuat atau mengedit objek Topic.
    """
    class Meta:
        model = Topic 
        fields = ['module', 'title', 'description', 'order','pretest'] 
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}), 
        }
        labels = {
            'module': 'Pilih Modul Induk',
            'title': 'Judul Topik',
            'description': 'Deskripsi Singkat (Opsional)',
            'order': 'Urutan Topik dalam Modul',
            'pretest': 'Pilih Kuis untuk Pre-test Topik Ini (Opsional)',
        }

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Filter pilihan dropdown 'pretest' agar hanya menampilkan kuis yang ditandai 'is_pretest'
            self.fields['pretest'].queryset = Quiz.objects.filter(is_pretest=True)

class LessonForm(forms.ModelForm):
    """
    Form Django untuk membuat atau mengedit objek Lesson.
    Biarkan ModelForm menangani field 'content' secara otomatis dari RichTextField.
    """
    class Meta:
        model = Lesson
        fields = ['title', 'content', 'order', 'minimum_reading_time'] 
        labels = {
            'title': 'Judul Pelajaran',
            'content': 'Isi Konten Pelajaran',
            'order': 'Urutan Pelajaran dalam Topik',
            'minimum_reading_time': 'Waktu Belajar Minimum (Menit)', # <-- Label baru
        }

class ModuleForm(forms.ModelForm):
    """
    Form Django untuk membuat atau mengedit objek Module.
    """
    class Meta:
        model = Module 
        fields = ['title', 'description', 'order']
        # Slug akan dibuat otomatis oleh model

        # Opsional: Widget & Label
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}), 
        }
        labels = {
            'title': 'Judul Modul',
            'description': 'Deskripsi Singkat (Opsional)',
            'order': 'Urutan Modul',
        }

class QuizForm(forms.ModelForm):
    """
    Form Django untuk membuat atau mengedit objek Quiz.
    """
    class Meta:
        model = Quiz 
        fields = ['title', 'description', 'order', 'pass_mark','time_limit_minutes','is_pretest'] 

        # Opsional: Widget & Label
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'pass_mark': forms.NumberInput(attrs={'min': 0, 'max': 100, 'step': 1}),
            'time_limit_minutes': forms.NumberInput(attrs={'min': 1})
        }
        labels = {
            'title': 'Judul Kuis',
            'description': 'Deskripsi Kuis (Opsional)',
            'order': 'Urutan Kuis dalam Topik',
            'pass_mark': 'Nilai Lulus Minimum (%)',
            'time_limit_minutes': 'Batas Waktu Pengerjaan (Menit)'
        }
        help_texts = {
            'pass_mark': 'Masukkan angka antara 0 sampai 100.',
        }

class QuestionForm(forms.ModelForm):
    """
    Form Django untuk membuat atau mengedit objek Question.
    """
    class Meta:
        model = Question # Berdasarkan model Question
        # Field yang ingin dimasukkan ke form
        # 'quiz' tidak dimasukkan karena akan di-set di view
        fields = ['text', 'order'] 
        
        # Opsional: Widget & Label
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4}), # Buat input teks pertanyaan lebih besar
        }
        labels = {
            'text': 'Teks Pertanyaan',
            'order': 'Urutan Pertanyaan dalam Kuis',
        }

class ChoiceForm(forms.ModelForm):
    """
    Form Django untuk satu Pilihan Jawaban (Choice).
    Akan digunakan di dalam formset.
    """
    class Meta:
        model = Choice
        # Field yang relevan untuk satu pilihan jawaban
        # 'question' tidak dimasukkan karena diatur oleh formset
        fields = ['text', 'is_correct'] 
        
        # Kosongkan widgets dan labels jika default sudah cukup,
        # atau tambahkan kustomisasi jika perlu.
        # Contoh:
        # widgets = {
        #     'text': forms.TextInput(attrs={'placeholder': 'Teks Pilihan Jawaban'}),
        # }
        # labels = {
        #     'text': '', # Kosongkan label jika tidak ingin tampil per baris
        #     'is_correct': 'Benar?' 
        # }