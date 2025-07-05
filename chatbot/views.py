# chatbot/views.py (FINAL - Rangkuman Selengkap Mungkin)

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings 
from django.utils.html import strip_tags, escape
import joblib
import os
import spacy 
import re
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from django.contrib.auth import get_user_model
from django.db.models import Q
import random
import markdown # Untuk konversi Markdown ke HTML

# Import untuk Summarization
from transformers import T5ForConditionalGeneration, T5Tokenizer
import torch

# Import model-model Anda
from learning.models import Lesson, Topic, Module
from articles.models import Article 
from .models import ChatMessage

User = get_user_model()

# --- Pemuatan Semua Model ---
MODEL_DIR = os.path.join(settings.BASE_DIR, 'chatbot', 'ml_models') 
VECTORIZER_PATH = os.path.join(MODEL_DIR, 'tfidf_vectorizer.joblib')
MATRIX_PATH = os.path.join(MODEL_DIR, 'tfidf_matrix.joblib')
IDENTIFIERS_PATH = os.path.join(MODEL_DIR, 'doc_identifiers.joblib')
tfidf_vectorizer, tfidf_matrix, doc_identifiers = None, None, None
try:
    if all(os.path.exists(p) for p in [VECTORIZER_PATH, MATRIX_PATH, IDENTIFIERS_PATH]):
        tfidf_vectorizer, tfidf_matrix, doc_identifiers = joblib.load(VECTORIZER_PATH), joblib.load(MATRIX_PATH), joblib.load(IDENTIFIERS_PATH)
        print("TF-IDF models loaded successfully.")
except Exception as e: print(f"Error loading TF-IDF models: {e}")

nlp_spacy = None
try:
    nlp_spacy = spacy.load('xx_ent_wiki_sm')
    print("spaCy model loaded successfully.")
except Exception as e: 
    print(f"Error loading spaCy model: {e}")
    nlp_spacy = None

SUMMARIZER_MODEL_NAME = 'cahya/t5-base-indonesian-summarization-cased'
summarizer_tokenizer, summarizer_model = None, None
try:
    summarizer_tokenizer = T5Tokenizer.from_pretrained(SUMMARIZER_MODEL_NAME)
    summarizer_model = T5ForConditionalGeneration.from_pretrained(SUMMARIZER_MODEL_NAME)
    print("Summarization model loaded successfully.")
except Exception as e: print(f"Error loading summarization model: {e}. Summarization disabled.")


# --- Fungsi Pembantu ---
def preprocess_text_minimal(text):
    if not text or not isinstance(text, str): return ""
    return strip_tags(text).lower()

# === PERUBAHAN DI FUNGSI INI untuk jawaban selengkap mungkin ===
def summarize_text(text, focus_term=None, max_length_target=510): # Set ke nilai tinggi (misal, dekat dengan input max)
    if not summarizer_model or not summarizer_tokenizer:
        return text # Fallback: kembalikan teks asli jika model tidak ada

    if focus_term:
        input_text = f"jelaskan secara detail, lengkap, dan mendalam tentang '{focus_term}' berdasarkan teks ini: {text}"
    else:
        input_text = f"buat rangkuman yang detail, lengkap, dan mendalam dari teks berikut: {text}"
    
    inputs = summarizer_tokenizer.encode(input_text, return_tensors='pt', max_length=512, truncation=True)
    
    summary_ids = summarizer_model.generate(
        inputs, 
        max_length=max_length_target, # Biarkan model menghasilkan sepanjang yang ia bisa hingga batas ini
        # min_length=30, # min_length bisa dihilangkan atau diset rendah agar tidak membatasi
        num_beams=5, 
        early_stopping=True,
        length_penalty=1.0 # Netral, tidak mendorong lebih panjang atau pendek secara artifisial
    )
    summary = summarizer_tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary
# === AKHIR PERUBAHAN DI FUNGSI INI ===

# --- Views ---
@login_required
def chat_interface(request):
    chat_history = ChatMessage.objects.filter(user=request.user).order_by('timestamp')
    context = {'chat_history': chat_history}
    return render(request, 'chatbot/chat_interface.html', context)


@login_required
@require_POST 
def process_chat_message(request):
    try:
        message_text_raw = request.POST.get('message', '').strip()
        if not message_text_raw: return JsonResponse({'error': 'Pesan kosong'}, status=400)
        
        ChatMessage.objects.create(user=request.user, message=escape(message_text_raw), is_user_message=True)

        bot_reply_raw = "Waduh, aku bingung nih. Bisa coba tanya yang lain?" 
        processed = False 
        
        cleaned_message = message_text_raw.lower().strip("!?. ")
        user_name = request.user.first_name or request.user.username

        # --- Logika Sapaan Mahasiswa (Prioritas Pertama) ---
        # (Gunakan blok sapaan lengkap Anda di sini, pastikan mengatur bot_reply_raw serta processed = True)
        sapaan_pagi = ["selamat pagi", "pagi", "met pagi"]
        sapaan_siang = ["selamat siang", "siang", "met siang"]
        sapaan_sore = ["selamat sore", "sore", "met sore"]
        sapaan_malam = ["selamat malam", "malam", "met malam", "malem"]
        sapaan_umum = ["halo", "hai", "hei", "woi", "bro", "sis", "kak", "permisi", "tes", "test", "testing", "punten"]
        
        balasan_sapaan_koleksi = {
            "pagi": ["Pagi juga, {nama}! Semangat buat hari ini ya!", "Pagii, {nama}! Udah ngopi belum? Hehe.", "Met pagi, {nama}! Semoga harimu menyenangkan."],
            "siang": ["Siang, {nama}! Lagi istirahat atau lagi ngejar deadline nih?", "Siang juga, {nama}! Panas ya? Mau tanya apa biar adem?", "Siang, {nama}! Jangan lupa makan siang ya."],
            "sore": ["Sore, {nama}! Udah mulai lelah ya? Yuk, tanya aku aja.", "Sore juga, {nama}! Bentar lagi kelar nih aktivitasnya.", "Met sore, {nama}! Semangat dikit lagi!"],
            "malam": ["Malam, {nama}! Masih semangat belajar? Keren!", "Malam juga, {nama}! Waktunya nge-chill atau nge-push tugas nih?", "Malem, {nama}! Jangan begadang ya, kecuali lagi seru-serunya belajar sama aku. 😉"]
        }
        tambahan_pertanyaan = f"Ada yang bisa aku bantu soal materi?"

        for kata_kunci in sapaan_pagi:
            if kata_kunci in cleaned_message:
                bot_reply_raw = f"{random.choice(balasan_sapaan_koleksi['pagi']).format(nama=user_name)} {tambahan_pertanyaan}"
                processed = True; break
        if not processed:
            for kata_kunci in sapaan_siang:
                if kata_kunci in cleaned_message:
                    bot_reply_raw = f"{random.choice(balasan_sapaan_koleksi['siang']).format(nama=user_name)} {tambahan_pertanyaan}"
                    processed = True; break
        if not processed:
            for kata_kunci in sapaan_sore:
                if kata_kunci in cleaned_message:
                    bot_reply_raw = f"{random.choice(balasan_sapaan_koleksi['sore']).format(nama=user_name)} {tambahan_pertanyaan}"
                    processed = True; break
        if not processed:
            for kata_kunci in sapaan_malam:
                if kata_kunci in cleaned_message:
                    bot_reply_raw = f"{random.choice(balasan_sapaan_koleksi['malam']).format(nama=user_name)} {tambahan_pertanyaan}"
                    processed = True; break
        if not processed:
            for kata_kunci in sapaan_umum:
                if kata_kunci in cleaned_message:
                    sapaan_balik = random.choice(["Halo juga!", "Hai!", "Yo! Ada apa nih?", "Sip! Mau tanya apa?", "Hola!"])
                    bot_reply_raw = f"{sapaan_balik} {tambahan_pertanyaan}"
                    processed = True; break

        pertanyaan_identitas = ["siapa kamu", "kamu siapa", "bot apa ini", "ini siapa", "kamu itu apa"]
        if not processed:
            for frasa in pertanyaan_identitas:
                if frasa in cleaned_message:
                    bot_reply_raw = random.choice([
                        "Aku Tutor Cerdas, chatbot kece yang siap bantu kamu ngerti materi Saintek. Tanya aja!",
                        "Kenalan dulu dong, aku Tutor Cerdas. Siap ngebantu kamu soal coding dan Saintek!",
                        "Panggil aja aku Tutor Cerdas. Misi utamaku adalah bikin kamu makin jago!"
                    ])
                    processed = True; break
        
        ucapan_terima_kasih = ["makasih", "terima kasih", "thanks", "thank you", "sip deh", "oke deh", "mantap", "nuhun", "matur nuwun"]
        if not processed:
            for frasa in ucapan_terima_kasih:
                if frasa in cleaned_message:
                    bot_reply_raw = random.choice([
                        "Sama-sama, {nama}! 😉", "Siap, gampang itu! Ada lagi?", 
                        "Santai, {nama}! Senang bisa bantu.", "Oke, {nama}, semangat terus ya belajarnya!",
                        "Dengan senang hati! Jangan sungkan tanya lagi."
                    ]).format(nama=user_name)
                    processed = True; break
        
        # --- Logika untuk permintaan "Contoh Kode" (Prioritas Setelah Sapaan) ---
        if not processed:
            keywords_contoh_kode = ["contoh kode", "struktur kode", "kode untuk", "berikan kode", "tunjukkan kode", "codingannya", "scriptnya"]
            topik_kode = None
            permintaan_kode_terdeteksi = False
            for keyword_ck in keywords_contoh_kode:
                if keyword_ck in cleaned_message:
                    permintaan_kode_terdeteksi = True
                    topik_kode_potensial = cleaned_message.split(keyword_ck, 1)[-1].strip()
                    if topik_kode_potensial:
                        topik_kode = " ".join(topik_kode_potensial.split()[:2])
                    break
            if permintaan_kode_terdeteksi and topik_kode:
                processed = True
                found_obj_with_code = Article.objects.filter(
                    Q(title__icontains=topik_kode) | Q(content__icontains=topik_kode),
                    content__icontains='<pre'
                ).first() or Lesson.objects.filter(
                    Q(title__icontains=topik_kode) | Q(content__icontains=topik_kode),
                    content__icontains='<pre'
                ).first()
                if found_obj_with_code:
                    bot_reply_raw = found_obj_with_code.content
                else:
                    def_obj = Article.objects.filter(title__icontains=topik_kode).first() or \
                              Lesson.objects.filter(title__icontains=topik_kode).first()
                    if def_obj:
                        summary = summarize_text(strip_tags(def_obj.content), focus_term=topik_kode)
                        bot_reply_raw = f"Maaf, {user_name}, contoh kode spesifik untuk '{topik_kode}' belum ada nih. Tapi ini ada penjelasan umumnya:\n\n{summary}"
                    else:
                        bot_reply_raw = f"Duh, {user_name}, aku belum nemu contoh kode ataupun penjelasan buat '{topik_kode}'. Coba yang lain ya."
            elif permintaan_kode_terdeteksi and not topik_kode:
                processed = True
                bot_reply_raw = "Contoh kode untuk apa ya? Tolong sebutkan topiknya."

        # --- Logika Pencarian Definisi (Menggunakan logika dari kode Anda sebelumnya) ---
        if not processed and nlp_spacy:
            keywords_definisi = ["jelaskan pengertian", "apa itu", "definisi", "jelaskan", "apa artinya"]
            subject_term = None
            for keyword in keywords_definisi:
                if keyword in cleaned_message:
                    term_part_text = cleaned_message.split(keyword, 1)[-1].strip(" :?.-")
                    if term_part_text:
                        subject_term = term_part_text.split(' ')[0]
                        break
            if subject_term:
                processed = True
                found_obj = Article.objects.filter(title__icontains=subject_term).first() or \
                            Lesson.objects.filter(title__icontains=subject_term).first()
                if found_obj:
                    original_content = found_obj.content
                    if '<pre' in original_content.lower():
                        bot_reply_raw = original_content
                    else:
                        summary = summarize_text(strip_tags(original_content), focus_term=subject_term)
                        bot_reply_raw = summary
                else:
                    bot_reply_raw = f"Maaf, {user_name}, aku belum nemu penjelasan spesifik soal '{subject_term}'."

        # --- Logika Pencarian TF-IDF (Menggunakan logika dari kode Anda sebelumnya) ---
        if not processed:
            if tfidf_vectorizer and tfidf_matrix is not None and doc_identifiers:
                try:
                    processed_query = preprocess_text_minimal(message_text_raw)
                    query_vector = tfidf_vectorizer.transform([processed_query])
                    cosine_similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
                    best_doc_index = np.argmax(cosine_similarities)
                    highest_score = cosine_similarities[best_doc_index]
                    if highest_score > 0.15:
                        doc_identifier = doc_identifiers[best_doc_index]
                        doc_type, doc_pk_str = doc_identifier.split('_pk_')
                        doc_pk = int(doc_pk_str)
                        obj = None
                        if doc_type == 'lesson': obj = Lesson.objects.filter(pk=doc_pk).first()
                        elif doc_type == 'article': obj = Article.objects.filter(pk=doc_pk).first()
                        if obj:
                            original_content = obj.content
                            if '<pre' in original_content.lower():
                                bot_reply_raw = original_content
                            else:
                                summary = summarize_text(strip_tags(original_content), focus_term=cleaned_message)
                                bot_reply_raw = summary
                except Exception as e_tfidf:
                    print(f"Error saat proses TF-IDF: {e_tfidf}")
                    bot_reply_raw = f"Duh, maaf, {user_name}, ada sedikit gangguan pas aku lagi nyari-nyari. Coba lagi ya."

        final_reply_for_display = bot_reply_raw 
        if not ('<pre' in bot_reply_raw.lower() and '</code></pre>' in bot_reply_raw.lower()):
            final_reply_for_display = markdown.markdown(
                bot_reply_raw, 
                extensions=['fenced_code', 'codehilite', 'nl2br', 'tables', 'sane_lists']
            )
        
        ChatMessage.objects.create(user=request.user, message=final_reply_for_display, is_user_message=False)
        return JsonResponse({'reply': final_reply_for_display})

    except Exception as e:
        print(f"FATAL ERROR di view process_chat_message: {e}")
        return JsonResponse({'reply': 'Duh, maaf banget nih, server lagi ada gangguan. Coba bentar lagi ya.'}, status=500)