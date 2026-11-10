"""
Accounts: the User table and the three kinds of account.

Class diagram: User is the parent of Student, Staff and Admin.
Database schema: one table called `user`, with a `role` column saying which kind it is.
Here, User is the real table, and Student, Staff and Admin are "proxy" classes:
they use the same table but only ever see the rows with their own role.
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class Role(models.TextChoices):
    STUDENT = 'student', 'Student'
    STAFF = 'staff', 'Staff'
    ADMIN = 'admin', 'Admin (security officer)'


class UserManager(BaseUserManager):
    """Creates accounts. set_password() stores only a one-way hash of the password (SY-P1)."""

    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('An email address is required.')
        user = self.model(email=self.normalize_email(email).lower(), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """The system owner: an Admin who can also open the /system-admin/ site."""
        extra_fields.setdefault('role', Role.ADMIN)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Every account: Student, Staff or Admin. Schema table: user."""

    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True,
                              error_messages={'unique': 'An account with this email already exists.'})
    # `password` (the hash) and `last_login` come from AbstractBaseUser.
    role = models.CharField(max_length=10, choices=Role.choices)
    admission_no = models.CharField(max_length=20, unique=True, null=True, blank=True,     # Students only
                                    error_messages={'unique': 'An account with this admission number already exists.'})
    staff_no = models.CharField(max_length=20, unique=True, null=True, blank=True,         # Staff only
                                error_messages={'unique': 'An account with this staff ID already exists.'})
    department = models.CharField(max_length=100, blank=True)                           # Staff only
    officer_no = models.CharField(max_length=20, unique=True, null=True, blank=True)    # Admin only
    is_verified = models.BooleanField(default=False)   # becomes True when the email link is clicked

    # Django's own switches:
    is_active = models.BooleanField(default=True)       # False = account switched off (never deleted)
    is_staff = models.BooleanField(
        default=False,
        help_text='Django word: may open the /system-admin/ site. It is NOT the Staff role.')
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'      # people log in with their email
    REQUIRED_FIELDS = ['name']

    class Meta:
        db_table = 'user'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.get_role_display()})'

    @property
    def is_student(self):
        return self.role == Role.STUDENT

    @property
    def is_staff_member(self):
        return self.role == Role.STAFF

    @property
    def is_admin_officer(self):
        return self.role == Role.ADMIN


class RoleManager(UserManager):
    """A manager that only sees one role, and gives new accounts that role."""

    use_in_migrations = False

    def __init__(self, role):
        super().__init__()
        self.role = role

    def get_queryset(self):
        return super().get_queryset().filter(role=self.role)

    def create_user(self, email, password=None, **extra_fields):
        extra_fields['role'] = self.role
        return super().create_user(email, password, **extra_fields)


class Student(User):
    """Student in the class diagram. Example: Student.objects.all() lists Students only."""
    objects = RoleManager(Role.STUDENT)

    class Meta:
        proxy = True


class Staff(User):
    """Staff (lecturers and non-teaching staff) in the class diagram."""
    objects = RoleManager(Role.STAFF)

    class Meta:
        proxy = True
        verbose_name_plural = 'staff'


class Admin(User):
    """Admin (security officer) in the class diagram. Created only by the system owner."""
    objects = RoleManager(Role.ADMIN)

    class Meta:
        proxy = True
