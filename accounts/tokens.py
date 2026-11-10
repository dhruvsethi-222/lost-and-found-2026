"""
The secret part of the email verification link.

Django already has a tool for making safe, time-limited links (it uses it for
"forgot password"). We reuse it. The token is built from the account id, the time
and whether the account is verified, so:
  - nobody can guess or forge it (it is signed with SECRET_KEY),
  - it stops working after PASSWORD_RESET_TIMEOUT (3 days, see settings.py),
  - it stops working once the account is verified (it cannot be used twice).
"""
from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    key_salt = 'accounts.tokens.EmailVerificationTokenGenerator'

    def _make_hash_value(self, user, timestamp):
        return f'{user.pk}{timestamp}{user.is_verified}{user.email}'


verification_token = EmailVerificationTokenGenerator()
