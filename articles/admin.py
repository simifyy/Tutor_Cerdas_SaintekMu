# articles/admin.py
from django.contrib import admin
from .models import Article # Impor model Article yang kita buat

# Membuat kelas konfigurasi untuk tampilan Article di admin
@admin.register(Article) # Cara modern mendaftarkan model dengan konfigurasi kustom
class ArticleAdmin(admin.ModelAdmin):
    # Menampilkan kolom-kolom ini di halaman daftar artikel admin
    list_display = ('title', 'slug', 'author', 'status', 'created_at')
    # Menambahkan filter di sisi kanan berdasarkan status dan tanggal dibuat
    list_filter = ('status', 'created_at', 'updated_at', 'author')
    # Menambahkan kotak pencarian berdasarkan judul dan konten
    search_fields = ('title', 'content')
    # Otomatis mengisi field 'slug' berdasarkan field 'title' saat mengetik di form admin
    prepopulated_fields = {'slug': ('title',)}
    # Menggunakan input field biasa (bukan dropdown) untuk author jika jumlah user banyak (opsional)
    # raw_id_fields = ('author',)
    # Menambahkan navigasi berdasarkan hirarki tanggal di atas daftar
    date_hierarchy = 'created_at'
    # Mengatur urutan default di halaman daftar admin
    ordering = ('status', '-created_at') # Urutkan berdasarkan status, lalu tanggal terbaru

# Cara lama mendaftarkan model (juga bisa, pilih salah satu):
# admin.site.register(Article, ArticleAdmin)