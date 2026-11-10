"""
Role checks (NFR-01: each role can only open its own pages).

Put @student_or_staff or @admin_only above a view and Django runs this check
before the view:
  - not logged in   -> sent to the right log-in page, then brought back,
  - wrong role      -> "Access denied" page (HTTP 403),
  - right role      -> the page opens.
"""
from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import resolve_url

from .models import Role


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                login_page = 'accounts:desk_login' if roles == (Role.ADMIN,) else 'accounts:login'
                return redirect_to_login(request.get_full_path(), resolve_url(login_page))
            if request.user.role not in roles:
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return wrapper
    return decorator


student_or_staff = role_required(Role.STUDENT, Role.STAFF)
admin_only = role_required(Role.ADMIN)
