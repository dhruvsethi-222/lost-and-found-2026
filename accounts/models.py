"""
Accounts: the table that holds every account.

How this matches the design:
  - Database schema: ONE table called `user`, with a `role` column that says
    whether the account is a student, staff or admin.
  - Class diagram: User is the parent of Student, Staff and Admin. The three
    small classes at the bottom of this file are those three classes. They use
    the same `user` table and each one only lists the accounts with its own role.
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class Role(models.TextChoices):
    """The three kinds of account. Left = stored in the database, right = shown on screen."""
    STUDENT = 'student', 'Student'
    STAFF = 'staff', 'Staff'
    ADMIN = 'admin', 'Admin (security officer)'


class UserManager(BaseUserManager):
    """Creates accounts. Used as User.objects.create_user(...)."""

    use_in_migrations = True      # lets Django's own set-up steps create accounts too

    def create_user(self, email, password=None, **other_fields):
        if not email:
            raise ValueError('An email address is required.')
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **other_fields)
        user.set_password(password)      # SY-P1: only a scrambled (hashed) password is stored
        user.save()
        return user

    def create_superuser(self, email, password=None, **other_fields):
        """The system owner: an Admin who can also open the /system-admin/ site."""
        other_fields.setdefault('role', Role.ADMIN)
        other_fields.setdefault('is_verified', True)
        other_fields.setdefault('is_staff', True)
        other_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **other_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Every account: Student, Staff or Admin. Database table: user."""

    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True,
                              error_messages={'unique': 'An account with this email already exists.'})
    # The `password` column (the hash) and `last_login` come from AbstractBaseUser.
    role = models.CharField(max_length=10, choices=Role.choices)

    # Students only
    admission_no = models.CharField(max_length=20, unique=True, null=True, blank=True,
                                    error_messages={'unique': 'An account with this admission number already exists.'})
    # Staff only
    staff_no = models.CharField(max_length=20, unique=True, null=True, blank=True,
                                error_messages={'unique': 'An account with this staff ID already exists.'})
    department = models.CharField(max_length=100, blank=True)
    # Admin only
    officer_no = models.CharField(max_length=20, unique=True, null=True, blank=True)

    is_verified = models.BooleanField(default=False)    # becomes True when the email link is clicked

    # Switches that Django itself uses:
    is_active = models.BooleanField(default=True)       # False = account switched off (never deleted)
    is_staff = models.BooleanField(
        default=False,
        help_text='Django word: may open the /system-admin/ site. It is NOT the Staff role.')
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'      # people log in with their email, not a username
    REQUIRED_FIELDS = ['name']

    class Meta:
        db_table = 'user'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.get_role_display()})'

    # Short questions the pages can ask, e.g. {% if user.is_admin_officer %}
    @property
    def is_student(self):
        return self.role == Role.STUDENT

    @property
    def is_staff_member(self):
        return self.role == Role.STAFF

    @property
    def is_admin_officer(self):
        return self.role == Role.ADMIN


# ---------------------------------------------------------------------------
# Student, Staff and Admin from the class diagram.
#
# "proxy = True" means: do not make a new table, use the `user` table.
# Each class has a small manager that keeps only the rows with its own role,
# so Student.objects.all() lists Students only.
#
# Accounts are always CREATED with User.objects.create_user(..., role=...).
# ---------------------------------------------------------------------------

class StudentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role=Role.STUDENT)


class StaffManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role=Role.STAFF)


class AdminManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role=Role.ADMIN)


class Student(User):
    """Student in the class diagram."""
    objects = StudentManager()

    class Meta:
        proxy = True


class Staff(User):
    """Staff (lecturers and non-teaching staff) in the class diagram."""
    objects = StaffManager()

    class Meta:
        proxy = True
        verbose_name_plural = 'staff'


class Admin(User):
    """Admin (security officer) in the class diagram. Created only by the system owner."""
    objects = AdminManager()

    class Meta:
        proxy = True
