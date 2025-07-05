# articles/views.py
from django.shortcuts import render
from django.views.generic import ListView, DetailView
from .models import Article 

class ArticleListView(ListView):
    """ Menampilkan daftar artikel yang sudah diterbitkan """
    model = Article
    template_name = 'articles/article_list.html'
    context_object_name = 'articles'
    paginate_by = 10 # Opsional: tampilkan 10 artikel per halaman

    def get_queryset(self):
        """ Hanya tampilkan artikel dengan status 'Terbit' """
        return Article.objects.filter(status=Article.Status.PUBLISHED).order_by('-created_at')

class ArticleDetailView(DetailView):
    """ Menampilkan detail satu artikel berdasarkan slug """
    model = Article
    template_name = 'articles/article_detail.html'
    context_object_name = 'article'

    def get_queryset(self):
        """ Pastikan hanya artikel 'Terbit' yang bisa diakses detailnya """
        # Jika ingin user login saja: self.request.user.is_authenticated
        # Untuk publik:
        return Article.objects.filter(status=Article.Status.PUBLISHED)
