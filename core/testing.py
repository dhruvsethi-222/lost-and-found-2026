"""Small helpers shared by the tests: ready-made accounts and a tiny photo."""
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from accounts.models import Role, User

PASSWORD = 'Campus-Pass-2026'


def make_student(email='jane@strathmore.edu', verified=True, **extra):
    extra.setdefault('admission_no', '227034')
    return User.objects.create_user(email, PASSWORD, role=Role.STUDENT, name='Jane Wanjiru', is_verified=verified, **extra)


def make_staff(email='otieno@strathmore.edu', verified=True, **extra):
    extra.setdefault('staff_no', 'S1043')
    return User.objects.create_user(email, PASSWORD, role=Role.STAFF, name='Peter Otieno',
                                    department='Computing', is_verified=verified, **extra)


def make_admin(email='achieng@strathmore.edu', **extra):
    extra.setdefault('officer_no', 'SO-001')
    return User.objects.create_user(email, PASSWORD, role=Role.ADMIN, name='Grace Achieng', is_verified=True, **extra)


def photo(name='wallet.png'):
    """A real (tiny) PNG image, made in memory."""
    buffer = io.BytesIO()
    Image.new('RGB', (8, 8), (20, 20, 20)).save(buffer, format='PNG')
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')
