"""
Creates an Admin (security officer) account. Only the system owner can run it,
because it runs on the server, not on a web page. Students and Staff therefore
have no way to create Admin accounts.

    python manage.py createofficer --email achieng@strathmore.edu --name "Grace Achieng" --officer-no SO-001
"""
import getpass

from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from accounts.models import Role, User


class Command(BaseCommand):
    help = 'Create an Admin (security officer) account.'

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True)
        parser.add_argument('--name', required=True)
        parser.add_argument('--officer-no', required=True)
        parser.add_argument('--password', help='Leave out to be asked for it (safer).')

    def handle(self, *args, **options):
        # 1. the email must not be used already
        email = options['email'].strip().lower()
        if User.objects.filter(email=email).exists():
            raise CommandError('An account with this email already exists.')
        # 2. ask for the password twice (nothing shows while typing)
        password = options['password']
        while not password:
            first = getpass.getpass('Password: ')
            if first != getpass.getpass('Password again: '):
                self.stderr.write('The passwords do not match.')
                continue
            password = first
        # 3. the password must pass the same rules as on the sign-up page
        try:
            password_validation.validate_password(password, User(name=options['name'], email=email))
        except ValidationError as error:
            raise CommandError(' '.join(error.messages))
        # 4. create the account: role admin, already verified
        officer = User.objects.create_user(email, password, role=Role.ADMIN, name=options['name'],
                                           officer_no=options['officer_no'], is_verified=True)
        self.stdout.write(self.style.SUCCESS(f'Admin account created for {officer.email}'))
