# accounts/decorators.py
from django.core.exceptions import PermissionDenied
from .models import User

def teacher_required(function):
    """
    Decorator untuk memastikan hanya pengguna dengan role 'TEACHER'
    yang bisa mengakses sebuah view.
    """
    def wrap(request, *args, **kwargs):
        # Cek apakah user sudah login DAN memiliki role TEACHER
        if request.user.is_authenticated and request.user.role == User.Role.TEACHER:
            # Jika ya, lanjutkan ke view aslinya
            return function(request, *args, **kwargs)
        else:
            # Jika tidak, tolak akses (akan menghasilkan error 403 Forbidden)
            raise PermissionDenied
            
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap