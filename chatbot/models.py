from django.db import models
from django.conf import settings # Untuk mengambil model User yang aktif

# Model yang sudah ada sebelumnya (biarkan saja)
class ChatbotSearchHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    query = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.query[:50]}"

# ---- TAMBAHKAN MODEL BARU DI BAWAH INI ----

class ChatMessage(models.Model):
    """
    Model untuk menyimpan setiap pesan dalam percakapan chatbot.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_messages', # Nama relasi balik dari User ke ChatMessage
        help_text="Pengguna yang terkait dengan pesan ini."
    )
    message = models.TextField(
        help_text="Teks pesan dari pengguna atau chatbot."
    )
    is_user_message = models.BooleanField(
        default=True, # Asumsi default adalah pesan dari user
        help_text="True jika pesan dari pengguna, False jika dari chatbot."
    )
    timestamp = models.DateTimeField(
        auto_now_add=True, # Otomatis set waktu saat pesan dibuat
        help_text="Waktu pesan dibuat."
    )

    class Meta:
        ordering = ['timestamp'] # Urutkan pesan berdasarkan waktu
        verbose_name = "Pesan Chat"
        verbose_name_plural = "Pesan Chat"

    def __str__(self):
        sender = "User" if self.is_user_message else "Bot"
        return f"{self.user.username} ({sender}): {self.message[:75]}" # Tampilkan potongan pesan