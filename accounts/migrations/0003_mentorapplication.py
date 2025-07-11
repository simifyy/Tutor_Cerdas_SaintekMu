# Generated by Django 5.2 on 2025-06-12 13:29

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_user_phone_number'),
    ]

    operations = [
        migrations.CreateModel(
            name='MentorApplication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=150, verbose_name='Nama Lengkap')),
                ('cv', models.FileField(upload_to='mentor_applications/cvs/', verbose_name='Curriculum Vitae (CV)')),
                ('other_document', models.FileField(blank=True, help_text='Opsional. Contoh: Sertifikat, Portofolio, dll.', null=True, upload_to='mentor_applications/docs/', verbose_name='Dokumen Pendukung')),
                ('status', models.CharField(choices=[('PENDING', 'Menunggu Persetujuan'), ('APPROVED', 'Disetujui'), ('REJECTED', 'Ditolak')], default='PENDING', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='mentor_application', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
