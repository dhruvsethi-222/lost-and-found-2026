"""
The site's address book: which part of the site answers which web address.
Each app keeps its own list of addresses in its own urls.py, included here.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = 'Lost and Found - system owner'
admin.site.site_title = 'Lost and Found'

urlpatterns = [
    path('', include('core.urls')),                 # home, My page, Security desk
    path('accounts/', include('accounts.urls')),    # register, verify, log in, log out
    path('items/', include('items.urls')),          # report items, record found items
    path('search/', include('search.urls')),        # search found items
    path('system-admin/', admin.site.urls),         # Django's built-in admin, for the system owner only
]

# On the laptop Django serves the uploaded photos itself; PythonAnywhere does it when live.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
