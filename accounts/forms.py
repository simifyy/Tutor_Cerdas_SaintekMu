# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm 
from .models import User, MentorApplication # Tambahkan import MentorApplication
from django.utils.translation import gettext_lazy as _ 

class RegistrationForm(UserCreationForm):
    full_name = forms.CharField(label="Nama Lengkap", max_length=150, required=True, help_text="Wajib diisi, mohon gunakan nama sesuai identitas.")
    email = forms.EmailField(label="Email", required=True, help_text='Wajib diisi.')
    phone_number = forms.CharField(label="Nomor Telepon", max_length=20, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'full_name', 'email', 'phone_number')
        widgets = { 
            'username': forms.TextInput(), 
        }
        labels = {
            'username': 'Username', 
        }

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        field_names = list(self.fields.keys()) 
        for field_name in field_names:
            field = self.fields.get(field_name)
            if field: 
                placeholder_text = ''
                if field_name == 'username': placeholder_text = 'Buat username unik'; field.label = 'Username'
                elif field_name == 'full_name': placeholder_text = 'Masukkan nama lengkap Anda'
                elif field_name == 'email': placeholder_text = 'contoh@gmail.com'; field.label = 'Email'
                elif field_name == 'phone_number': placeholder_text = 'Contoh: 628123xxxxxxx (Opsional)'; field.label = 'Nomor Telepon'
                elif field_name == 'password1': placeholder_text = 'Buat password (minimal 8 karakter)'; field.label = "Password" 
                elif field_name == 'password2': placeholder_text = 'Ulangi password di atas'; field.label = "Konfirmasi Password" 
                field.widget.attrs.update({'class': 'form-control form-control-lg', 'placeholder': placeholder_text})
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists(): raise forms.ValidationError("Email ini sudah terdaftar...")
        return email

    def save(self, commit=True):
        user = super().save(commit=False); full_name = self.cleaned_data.get('full_name'); first_name = full_name; last_name = ""
        if ' ' in full_name: parts = full_name.split(' ', 1); first_name = parts[0]; last_name = parts[1]
        user.first_name = first_name; user.last_name = last_name
        if 'phone_number' in self.cleaned_data: user.phone_number = self.cleaned_data.get('phone_number') 
        if commit: user.save()
        return user

class ProfileUpdateForm(forms.ModelForm):
    full_name = forms.CharField(label="Nama Lengkap", max_length=150, required=True, help_text="...", widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, help_text=_('Wajib diisi.'), widget=forms.EmailInput(attrs={'class': 'form-control'}))
    username = forms.CharField(required=True, disabled=True, widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': True})) 
    phone_number = forms.CharField(label="Nomor Telepon", max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    field_order = ['full_name', 'profile_picture', 'expertise', 'bio', 'email', 'phone_number']

    class Meta: 
        model = User
        fields = ['profile_picture', 'bio', 'expertise', 'email', 'phone_number']
        
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'expertise': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contoh: Web Development, Desain Grafis'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'bio': "Deskripsi Singkat (Bio)",
            'expertise': "Bidang Keahlian/Minat",
            'phone_number': "Nomor Telepon (WhatsApp)",
            'profile_picture': "Ubah Foto Profil",
        }
        help_texts = {
            'profile_picture': 'Disarankan mengunggah foto dengan rasio 1:1 (persegi).',
            'bio': 'Tuliskan deskripsi singkat tentang diri Anda (maksimal 250 karakter).',
        }

    def __init__(self, *args, **kwargs):
        super(ProfileUpdateForm, self).__init__(*args, **kwargs); initial_full_name = self.instance.get_full_name(); self.fields['full_name'].initial = initial_full_name
        self.fields['username'].initial = self.instance.username; self.fields['email'].initial = self.instance.email; self.fields['phone_number'].initial = self.instance.phone_number
    def clean_email(self):
        email = self.cleaned_data.get('email');
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists(): raise forms.ValidationError(_("..."))
        return email
    def save(self, commit=True):
        user = super().save(commit=False); full_name = self.cleaned_data.get('full_name'); first_name = full_name; last_name = ""
        if ' ' in full_name: parts = full_name.split(' ', 1); first_name = parts[0]; last_name = parts[1]
        user.first_name = first_name; user.last_name = last_name
        if commit: user.save()
        return user

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="Username", strip=False, widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control form-control-lg', 'placeholder': 'Username atau Email'}))
    password = forms.CharField(label="Password", strip=False, widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'class': 'form-control form-control-lg', 'placeholder': 'Password'}))

# --- KODE BARU DIMULAI DI SINI ---

class MentorUserCreationForm(UserCreationForm):
    """Form untuk membuat akun user dasar bagi calon mentor."""
    email = forms.EmailField(label="Email", required=True, help_text='Wajib diisi.')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email') # Hanya butuh username, email, dan password
        
    def __init__(self, *args, **kwargs):
        super(MentorUserCreationForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control form-control-lg'
            if field_name == 'username':
                field.widget.attrs['placeholder'] = 'Buat username unik'
            elif field_name == 'email':
                field.widget.attrs['placeholder'] = 'contoh@gmail.com'
            elif field_name == 'password1':
                field.widget.attrs['placeholder'] = 'Buat password'
                field.label = "Password"
            elif field_name == 'password2':
                field.widget.attrs['placeholder'] = 'Ulangi password'
                field.label = "Konfirmasi Password"
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email ini sudah terdaftar.")
        return email

class MentorApplicationForm(forms.ModelForm):
    """Form untuk data spesifik lamaran mentor."""
    # Definisikan field declaration secara eksplisit agar bisa diwajibkan
    declaration = forms.BooleanField(
        required=True, # Ini akan memaksa pengguna untuk mencentang kotak
        label="Saya menyatakan bahwa data yang saya isi adalah benar dan dapat dipertanggungjawabkan."
    )
    
    class Meta:
        model = MentorApplication
        # Daftarkan semua field yang ingin ditampilkan di form
        # ModelForm akan secara otomatis membuat field yang wajib diisi menjadi required=True di HTML
        fields = [
            'full_name', 'gender', 'date_of_birth', 'whatsapp_number', 'address',
            'profile_picture', 'expertise', 'bio',
            'education_level', 'institution_name', 'major', 'graduation_year',
            'cv', 'portfolio_pdf', 'github_link', 'certificate', 'intro_video',
            'declaration'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'graduation_year': forms.NumberInput(attrs={'min': 1980, 'max': 2025}),
        }

        help_texts = {
            'profile_picture': 'Disarankan mengunggah foto dengan rasio 1:1 (persegi) agar pas dan tidak terpotong.',
            'bio': 'Tuliskan perkenalan singkat (maksimal 250 karakter) untuk ditampilkan di profil publik Anda.',
        }

    def __init__(self, *args, **kwargs):
        super(MentorApplicationForm, self).__init__(*args, **kwargs)
        # Menambahkan kelas bootstrap untuk styling
        for field_name, field in self.fields.items():
            if field_name != 'declaration' and field_name != 'gender':
                field.widget.attrs.update({'class': 'form-control'})