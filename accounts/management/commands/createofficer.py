"""
Creates an Admin (security officer) account. Only the system owner can run it,
because it runs on the server, not on a web page. Students and Staff therefore
have no way to create Admin accounts.

    python manage.py createofficer --email officer@campus.ac.ke --name "Grace Achieng" --officer-no SO-001
"""
import getpass

from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from accounts.models import Admin, User


class Command(BaseCommand):
    help = 'Create an Admin (security officer) account.'

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True)
        parser.add_argument('--name', required=True)
        parser.add_argument('--officer-no', required=True)
        parser.add_argument('--password', help='Leave out to be asked for it (safer).')

    def handle(self, *args, **options):
        email = options['email'].strip().lower()
        if User.objects.filter(email=email).exists():
            raise CommandError('An account with this email already exists.')
        password = options['password']
        while not password:
            first = getpass.getpass('Password: ')
            if first != getpass.getpass('Password again: '):
                self.stderr.write('The passwords do not match.')
                continue
            password = first
        try:
            password_validation.validate_password(password, User(name=options['name'], email=email))
        except ValidationError as error:
            raise CommandError(' '.join(error.messages))
        officer = Admin.objects.create_user(email, password, name=options['name'],
                                            officer_no=options['officer_no'], is_verified=True)
        self.stdout.write(self.style.SUCCESS(f'Admin account created for {officer.email}'))
