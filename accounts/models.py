# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

class User(AbstractUser):
    # Kita tambahkan pilihan peran (role)
    class Role(models.TextChoices):
        USER = 'USER', 'User'          # Pengguna biasa
        TEACHER = 'TEACHER', 'Teacher'  # Pengajar/Guru
        ADMIN = 'ADMIN', 'Admin'        

    role = models.CharField(max_length=50, choices=Role.choices, default=Role.USER)

    phone_number = models.CharField(
        "Nomor Telepon (WhatsApp)", # verbose_name
        max_length=20,              # Panjang maksimal (sesuaikan jika perlu)
        blank=True,                 # Izinkan field ini kosong di form
        null=True,                  # Izinkan nilai NULL di database (penting untuk field baru)
        help_text="Format: 62812... (diawali kode negara, tanpa + atau spasi/strip)" 
    )

    profile_picture = models.ImageField(
        "Foto Profil", 
        upload_to='profile_pics/', 
        null=True, 
        blank=True
    )
    bio = models.TextField("Deskripsi Singkat (Bio)", max_length=250, blank=True)
    expertise = models.CharField("Bidang Keahlian", max_length=100, blank=True)

    def __str__(self):
        return self.username


class MentorApplication(models.Model):
    wa_validator = RegexValidator(
        regex=r'^62\d{9,15}$',
        message="Format nomor WhatsApp tidak valid. Harap gunakan format 628xxxxxx, tanpa spasi atau tanda '+'."
    )
    
    # --- Data Internal ---
    STATUS_CHOICES = (
        ('PENDING', 'Menunggu Persetujuan'),
        ('REVIEW', 'Sedang Direview'),
        ('APPROVED', 'Disetujui'),
        ('REJECTED', 'Ditolak'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mentor_application')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    # --- A. Informasi Pribadi (Semua Wajib) ---
    GENDER_CHOICES = (('L', 'Laki-laki'), ('P', 'Perempuan'))
    full_name = models.CharField("Nama Lengkap", max_length=150) # Wajib
    gender = models.CharField("Jenis Kelamin", max_length=1, choices=GENDER_CHOICES) # Wajib
    date_of_birth = models.DateField("Tanggal Lahir") # Wajib
    whatsapp_number = models.CharField("Nomor WhatsApp Aktif", max_length=20, validators=[wa_validator]) # Wajib dengan validator
    address = models.TextField("Alamat Domisili") # Wajib
    profile_picture = models.ImageField("Foto Profil Anda", upload_to='applicant_pics/') # Wajib diisi saat daftar
    expertise = models.CharField("Bidang Keahlian Utama", max_length=100, help_text="Contoh: Fisika Kuantum, Kalkulus, Pemrograman Python") # Wajib
    bio = models.TextField("Deskripsi Singkat / Bio", max_length=250, help_text="Tuliskan perkenalan singkat tentang diri Anda untuk ditampilkan di profil.") # Wajib
    
    # --- B. Latar Belakang Pendidikan (Semua Wajib) ---
    EDUCATION_CHOICES = (('SMA', 'SMA/Sederajat'), ('D3', 'Diploma 3'), ('S1', 'Sarjana (S1)'), ('S2', 'Magister (S2)'))
    education_level = models.CharField("Pendidikan Terakhir", max_length=5, choices=EDUCATION_CHOICES) # Wajib
    institution_name = models.CharField("Nama Institusi Pendidikan", max_length=255) # Wajib
    major = models.CharField("Jurusan", max_length=100) # Wajib
    graduation_year = models.PositiveIntegerField("Tahun Lulus") # Wajib

    # --- C. Dokumen Pendukung (CV Wajib, lainnya Opsional) ---
    cv = models.FileField("Unggah CV (PDF)", upload_to='mentor_applications/cvs/') # Wajib
    portfolio_pdf = models.FileField("Unggah Portofolio (PDF)", upload_to='mentor_applications/portfolios/', blank=True, null=True) # Opsional
    github_link = models.URLField("Link GitHub/Portofolio Online", blank=True, null=True) # Opsional
    certificate = models.FileField("Unggah Sertifikat", upload_to='mentor_applications/certificates/', blank=True, null=True) # Opsional
    intro_video = models.FileField("Unggah Video Perkenalan", upload_to='mentor_applications/videos/', blank=True, null=True, help_text="Opsional, ukuran maks 50MB") # Opsional

    # --- D. Pernyataan (Wajib dicentang di form) ---
    declaration = models.BooleanField("Pernyataan Kebenaran Data", default=False)

    def __str__(self):
        return f'Lamaran dari: {self.full_name} ({self.get_status_display()})'