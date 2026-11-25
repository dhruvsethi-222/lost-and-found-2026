"""
Moves the five fictional demo accounts from the old campus email addresses to @strathmore.edu.

It changes only the email address, in place, so each account keeps its id, role, password,
reports, claims and posts. It is used by the migration accounts/0002 and by its tests.
"""

# old address, new address, and the name and role the demo account must have
DEMO_ACCOUNTS = [
    ('jane@students.campus.ac.ke', 'jane@strathmore.edu', 'Jane Wanjiru', 'student'),
    ('brian@students.campus.ac.ke', 'brian@strathmore.edu', 'Brian Kamau', 'student'),
    ('amina@students.campus.ac.ke', 'amina@strathmore.edu', 'Amina Hassan', 'student'),
    ('otieno@campus.ac.ke', 'otieno@strathmore.edu', 'Peter Otieno', 'staff'),
    ('achieng@campus.ac.ke', 'achieng@strathmore.edu', 'Grace Achieng', 'admin'),
]


def move_demo_accounts(User):
    """
    Updates each demo account that still uses its old address.
    Returns a list of messages about accounts that were left alone, so they can be checked by hand.
    """
    notes = []
    for old_email, new_email, name, role in DEMO_ACCOUNTS:
        account = User.objects.filter(email=old_email).first()
        if account is None:
            continue                                   # not in this database: nothing to do

        # Only change it if it really is the fictional demo account.
        if account.name != name or account.role != role:
            notes.append(f'Not changed: {old_email} is not the demo account {name} ({role}). Check it by hand.')
            continue

        # Never give one address to two accounts.
        if User.objects.filter(email=new_email).exclude(pk=account.pk).exists():
            notes.append(f'Not changed: {old_email}, because {new_email} is already used by another account.')
            continue

        account.email = new_email
        account.save(update_fields=['email'])
    return notes
