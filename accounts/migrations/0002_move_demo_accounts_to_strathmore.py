"""
Moves the fictional demo accounts (Jane, Brian, Amina, Peter, Grace) to @strathmore.edu, in place.
Real accounts are never touched. Accounts that could not be moved are listed when migrate runs.
"""
from django.db import migrations

from accounts.demo_accounts import move_demo_accounts


def forwards(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    for note in move_demo_accounts(User):
        print(f'\n  {note}')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        # Going back does nothing: the accounts keep their new addresses.
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
