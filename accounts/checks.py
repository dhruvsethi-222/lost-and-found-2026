"""
A start-up check (shown by runserver and migrate): sign-up must allow exactly @strathmore.edu.

An older .env file may still list the old example endings, e.g. students.campus.ac.ke.
This check prints a warning so the line can be fixed before a demo.
"""
from django.conf import settings
from django.core.checks import Warning, register

AGREED_ENDINGS = ['strathmore.edu']


@register()
def check_email_endings(app_configs, **kwargs):
    warnings = []
    for name in ('STUDENT_EMAIL_DOMAINS', 'STAFF_EMAIL_DOMAINS'):
        if getattr(settings, name) != AGREED_ENDINGS:
            warnings.append(Warning(
                f'{name} is {", ".join(getattr(settings, name))}, so sign-up does not require @strathmore.edu.',
                hint=f'Open .env and change the line to {name}=strathmore.edu, then restart the site.',
                id='accounts.W001'))
    return warnings
