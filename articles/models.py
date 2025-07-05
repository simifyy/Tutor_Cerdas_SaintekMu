from django.db import models
from django.conf import settings  # Untuk merujuk ke model User kustom
from django.utils.text import slugify  # Untuk membuat slug URL
from django.utils import timezone  # Untuk zona waktu


class Article(models.Model):
    """ Model untuk menyimpan artikel blog/pembelajaran """

    # Pilihan status dalam Bahasa Indonesia
    class Status(models.TextChoices):
        DRAFT = 'DF', 'Draf'          # Label Bahasa Indonesia
        PUBLISHED = 'PB', 'Terbit'    # Label Bahasa Indonesia

    # Pilihan Kategori Artikel
    class Category(models.TextChoices):
        UMUM = 'UM', 'Umum'
        DEFINISI = 'DF', 'Definisi'
        TUTORIAL = 'TU', 'Tutorial'
        LAIN_LAIN = 'LL', 'Lain-lain'

    # Menambahkan verbose_name ke setiap field
    title = models.CharField(max_length=200, verbose_name="Judul")
    slug = models.SlugField(max_length=250, unique=True, blank=True, verbose_name="Slug (untuk URL)")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,  # Jika penulis dihapus, artikel tidak ikut terhapus
        null=True,                  # Izinkan field ini kosong di DB
        related_name='articles',    # Nama untuk relasi balik dari User
        verbose_name="Penulis"      # Label Bahasa Indonesia
    )
    content = models.TextField(verbose_name="Isi Konten")
    status = models.CharField(
        max_length=2,
        choices=Status.choices,
        default=Status.DRAFT,        # Default adalah Draf
        verbose_name="Status"        # Label Bahasa Indonesia
    )
    category = models.CharField(
        max_length=2,
        choices=Category.choices,
        default=Category.UMUM,
        verbose_name="Kategori Artikel"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Waktu Dibuat")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Waktu Diperbarui")

    class Meta:
        ordering = ['-created_at']  # Urutkan artikel terbaru dulu
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status']),
            models.Index(fields=['category']),  # Tambahkan index untuk kategori
        ]
        # Menambahkan nama model dalam Bahasa Indonesia
        verbose_name = "Artikel"
        verbose_name_plural = "Artikel"  # Bentuk jamak

    def __str__(self):
        # Representasi string objek ini adalah judulnya
        return self.title

    def save(self, *args, **kwargs):
        # Otomatis buat slug dari judul jika slug kosong saat menyimpan
        if not self.slug:
            self.slug = slugify(self.title)
            # Di aplikasi nyata, mungkin perlu menambahkan logika
            # untuk memastikan slug tetap unik jika ada judul yang sama.
            # Misalnya menambahkan angka atau ID. Untuk sekarang, ini cukup.
        super().save(*args, **kwargs)  # Panggil metode save asli