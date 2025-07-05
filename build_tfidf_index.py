# build_tfidf_index.py

import os
import django
import joblib 
import spacy
from django.utils.html import strip_tags
from sklearn.feature_extraction.text import TfidfVectorizer
import re

# 1. Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings') 
print("Setting up Django...")
django.setup()
print("Django setup complete.")

# 2. Import Model Django 
try:
    from learning.models import Lesson, Topic, Module 
    from articles.models import Article 
    print("Django models imported successfully.")
except ImportError as e:
    print(f"Error importing Django models: {e}")
    exit()
except Exception as e:
    print(f"An unexpected error occurred during model import: {e}")
    exit()


# 3. Fungsi Preprocessing Teks (SANGAT MINIMAL)
def preprocess_text_minimal(text):
    """HANYA hapus HTML dan jadikan lowercase."""
    if not text:
        return ""
    try: 
       text = strip_tags(text) 
    except Exception as e_strip:
        print(f"  Warning: strip_tags failed for a text snippet: {e_strip}")
        pass 
    # Hanya lowercase, tidak ada filter lain
    return text.lower() 

# 4. Kumpulkan Corpus (Kumpulan Teks) dan Penanda Dokumen
print("Collecting documents from database...")
corpus = [] 
document_identifiers = [] 
processed_count = 0

# Ambil dari Lessons
try:
    lessons = Lesson.objects.all()
    print(f"Processing {lessons.count()} lessons...")
    for i, lesson in enumerate(lessons): 
        full_text = f"{lesson.title or ''} {lesson.content or ''}" 
        
        # --- PRINT DEBUG Teks Mentah ---
        if i < 3: # Cetak 3 contoh teks mentah pertama
            print(f"  [Lesson PK {lesson.pk}] RAW text sample: '{full_text[:300]}...'") 
        # --- AKHIR PRINT DEBUG ---

        # Gunakan preprocessing minimal
        processed = preprocess_text_minimal(full_text) 

        if i < 5: # Cetak 5 hasil proses pertama
             print(f"  [Lesson PK {lesson.pk}] MINIMALLY Processed text sample: '{processed[:200]}...'") 
        if processed: 
            corpus.append(processed)
            document_identifiers.append(f"lesson_pk_{lesson.pk}")
            processed_count += 1 
    print("Finished processing lessons.")
except Exception as e:
    print(f"Error processing lessons: {e}")

# Ambil dari Articles (jika ada)
try:
    articles = Article.objects.filter(status=Article.Status.PUBLISHED) 
    print(f"Processing {articles.count()} articles...")
    for i, article in enumerate(articles): 
        full_text = f"{article.title or ''} {article.content or ''}" 

        # --- PRINT DEBUG Teks Mentah ---
        if i < 3: # Cetak 3 contoh teks mentah pertama
            print(f"  [Article PK {article.pk}] RAW text sample: '{full_text[:300]}...'") 
        # --- AKHIR PRINT DEBUG ---

        # Gunakan preprocessing minimal
        processed = preprocess_text_minimal(full_text) 

        if i < 5: 
             print(f"  [Article PK {article.pk}] MINIMALLY Processed text sample: '{processed[:200]}...'") 
        if processed:
            corpus.append(processed)
            document_identifiers.append(f"article_pk_{article.pk}")
            processed_count += 1 
    print("Finished processing articles.")
except Exception as e:
     print(f"Error processing articles: {e}")

# Print Debug Hasil Corpus
print(f"\nTotal documents successfully processed with content: {processed_count}")
print(f"Total items in corpus list: {len(corpus)}")
if corpus:
     print("First few items in corpus (minimal processing):")
     for item in corpus[:3]:
         print(f"  - '{item[:200]}...'")

if not corpus:
    print("Error: Corpus is still empty even with minimal processing. Check source content.")
    exit()

# 5. Buat dan Latih TF-IDF Vectorizer (tetap pakai min_df=1)
print("\nBuilding TF-IDF index...")
try:
    print("Vectorizer settings: min_df=1") 
    vectorizer = TfidfVectorizer(min_df=1) # Tetap pakai min_df=1
    
    tfidf_matrix = vectorizer.fit_transform(corpus)
    print(f"TF-IDF matrix created with shape: {tfidf_matrix.shape}") 
    if len(vectorizer.vocabulary_) == 0:
        print("ERROR: Vocabulary is STILL empty! Problem might be with the source content itself.")
    else:
        print(f"Vocabulary size: {len(vectorizer.vocabulary_)}")

except ValueError as ve: 
    print(f"ERROR during TF-IDF vectorization: {ve}")
    exit()
except Exception as e:
    print(f"An unexpected error occurred during TF-IDF vectorization: {e}")
    exit()

# Jika berhasil sampai sini (vocabulary tidak kosong), lanjutkan menyimpan
if len(vectorizer.vocabulary_) > 0:
    # 6. Simpan Hasil Indexing ke File
    output_dir = 'chatbot/ml_models' 
    os.makedirs(output_dir, exist_ok=True) 
    vectorizer_path = os.path.join(output_dir, 'tfidf_vectorizer.joblib')
    matrix_path = os.path.join(output_dir, 'tfidf_matrix.joblib')
    identifiers_path = os.path.join(output_dir, 'doc_identifiers.joblib')
    print(f"Saving TF-IDF vectorizer to {vectorizer_path}...")
    joblib.dump(vectorizer, vectorizer_path)
    print(f"Saving TF-IDF matrix to {matrix_path}...")
    joblib.dump(tfidf_matrix, matrix_path)
    print(f"Saving document identifiers to {identifiers_path}...")
    joblib.dump(document_identifiers, identifiers_path)
    print("\nTF-IDF indexing complete! Files saved successfully.")
    print(f"Total documents indexed: {len(document_identifiers)}")
    print(f"Vocabulary size: {len(vectorizer.vocabulary_)}")
else:
     print("\nExiting without saving files due to empty vocabulary.")