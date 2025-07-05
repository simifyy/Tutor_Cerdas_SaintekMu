# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.shortcuts import redirect
from django.contrib.auth.models import Group
from .models import User, MentorApplication

# --- Bagian Custom User Admin (Tidak Diubah) ---
class CustomUserAdmin(UserAdmin):
    # ... (isi kelas ini tetap sama seperti sebelumnya)
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'phone_number')
    fieldsets = list(UserAdmin.fieldsets)
    personal_info_index = -1
    for i, fieldset in enumerate(fieldsets):
        if fieldset and fieldset[0] == 'Personal info':
            personal_info_index = i
            break
    if personal_info_index != -1:
        original_fields = list(fieldsets[personal_info_index][1]['fields'])
        if 'role' not in original_fields:
            original_fields.append('role')
        if 'phone_number' not in original_fields:
            original_fields.append('phone_number')
        fieldsets[personal_info_index] = ('Personal info', {'fields': tuple(original_fields)})
    else:
        fieldsets.append(('Informasi Tambahan', {'fields': ('role', 'phone_number')}))
    list_filter = UserAdmin.list_filter + ('role',)
    search_fields = UserAdmin.search_fields + ('phone_number',)

admin.site.register(User, CustomUserAdmin)


# --- FUNGSI-FUNGSI ADMIN ACTION ---

@admin.action(description="Setujui lamaran & ubah role menjadi Pengajar")
def approve_applications(modeladmin, request, queryset):
    for application in queryset:
        user = application.user
        
        user.phone_number = application.whatsapp_number
        user.profile_picture = application.profile_picture 
        user.bio = application.bio                         
        user.expertise = application.expertise             
        
        # Lanjutkan dengan mengubah role dan status aktif
        user.role = User.Role.TEACHER
        user.is_active = True
        user.save() # Simpan semua perubahan pada user
        
        # Ubah status lamaran
        application.status = 'APPROVED'
        application.save()
        
    modeladmin.message_user(request, f"{queryset.count()} lamaran berhasil disetujui.")

@admin.action(description="Tandai lamaran sedang direview")
def mark_as_reviewing(modeladmin, request, queryset):
    queryset.update(status='REVIEW')
    modeladmin.message_user(request, f"{queryset.count()} lamaran ditandai 'Sedang Direview'.")

@admin.action(description="Tolak lamaran & nonaktifkan akun")
def reject_applications(modeladmin, request, queryset):
    for application in queryset:
        user = application.user
        user.is_active = False
        user.save()

        application.status = 'REJECTED'
        application.save()
    modeladmin.message_user(request, f"{queryset.count()} lamaran ditolak dan akun pengguna dinonaktifkan.")


@admin.register(MentorApplication)
class MentorApplicationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('user__username', 'full_name')
    actions = [approve_applications, mark_as_reviewing, reject_applications]
    
    # Membuat field menjadi read-only di halaman detail
    def get_readonly_fields(self, request, obj=None):
        if obj: 
            # Ambil semua nama field dari model
            all_fields = [field.name for field in self.model._meta.fields]
            # Hapus 'status' dari daftar read-only agar bisa diedit
            all_fields.remove('status')
            return all_fields
        return []
    
    # Override metode change_view untuk menangani form kustom kita
    def change_view(self, request, object_id, form_url='', extra_context=None):
        # Cek jika form kustom kita yang di-submit
        if request.method == 'POST' and '_update_status' in request.POST:
            # Ambil objek lamaran yang sedang dilihat
            application = self.get_object(request, object_id)
            new_status = request.POST.get('new_status')

            if application and new_status:
                if new_status == 'REVIEW':
                    application.status = 'REVIEW'
                    application.save()
                    self.message_user(request, "Status lamaran telah diubah menjadi 'Sedang Direview'.")
                
                elif new_status == 'REJECTED':
                    user = application.user
                    user.is_active = False
                    user.save()
                    application.status = 'REJECTED'
                    application.save()
                    self.message_user(request, "Lamaran telah ditolak dan akun pengguna dinonaktifkan.")

                elif new_status == 'APPROVED':
                    user = application.user
                    user.phone_number = application.whatsapp_number
                    user.profile_picture = application.profile_picture
                    user.bio = application.bio
                    user.expertise = application.expertise
                    user.role = User.Role.TEACHER
                    user.is_active = True
                    user.save()
                    application.status = 'APPROVED'
                    application.save()
                    self.message_user(request, "Lamaran telah disetujui. Akun pengguna telah diubah menjadi Mentor.")
                
                # Arahkan kembali ke halaman yang sama untuk melihat perubahan
                return redirect(request.path)

        # Jika bukan form kustom kita, jalankan perilaku default
        return super().change_view(request, object_id, form_url, extra_context=extra_context)
    
    admin.site.unregister(Group)