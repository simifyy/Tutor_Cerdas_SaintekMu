# Generated by Django 5.2 on 2025-04-10 15:49

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Module',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=150, unique=True, verbose_name='Judul Modul')),
                ('slug', models.SlugField(blank=True, max_length=170, unique=True, verbose_name='Slug (untuk URL)')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Deskripsi Singkat')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Urutan')),
            ],
            options={
                'verbose_name': 'Modul',
                'verbose_name_plural': 'Modul',
                'ordering': ['order', 'title'],
            },
        ),
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=150, verbose_name='Judul Topik')),
                ('slug', models.SlugField(blank=True, max_length=170, unique=True, verbose_name='Slug (untuk URL)')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Deskripsi Singkat')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Urutan')),
                ('module', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='topics', to='learning.module', verbose_name='Modul Induk')),
            ],
            options={
                'verbose_name': 'Topik',
                'verbose_name_plural': 'Topik',
                'ordering': ['module', 'order', 'title'],
            },
        ),
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=150, verbose_name='Judul Pelajaran')),
                ('slug', models.SlugField(blank=True, max_length=170, unique=True, verbose_name='Slug (untuk URL)')),
                ('content', models.TextField(verbose_name='Isi Konten Pelajaran')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Urutan')),
                ('topic', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lessons', to='learning.topic', verbose_name='Topik Induk')),
            ],
            options={
                'verbose_name': 'Pelajaran',
                'verbose_name_plural': 'Pelajaran',
                'ordering': ['topic', 'order', 'title'],
            },
        ),
        migrations.CreateModel(
            name='UserLessonProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('completed_at', models.DateTimeField(auto_now_add=True, verbose_name='Waktu Selesai')),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='progress_records', to='learning.lesson', verbose_name='Pelajaran')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lesson_progress', to=settings.AUTH_USER_MODEL, verbose_name='Pengguna')),
            ],
            options={
                'verbose_name': 'Progres Pelajaran Pengguna',
                'verbose_name_plural': 'Progres Pelajaran Pengguna',
                'ordering': ['user', '-completed_at'],
                'unique_together': {('user', 'lesson')},
            },
        ),
    ]
