# Generated by Django 5.2 on 2025-04-13 23:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='phone_number',
            field=models.CharField(blank=True, help_text='Format: 62812... (diawali kode negara, tanpa + atau spasi/strip)', max_length=20, null=True, verbose_name='Nomor Telepon (WhatsApp)'),
        ),
    ]
