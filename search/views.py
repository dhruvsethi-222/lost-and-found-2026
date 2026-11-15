"""
Search found items (ST-P5, SF-P5) and show the results (ST-O2, SF-O2).
Each result has a Claim button (ST-P6, SF-P6).

Privacy (NFR-02): this page reads only the public columns of the found_item
table. It never reads the verification_detail table, so serial numbers, marks
and contents cannot appear here, whatever is typed in the search box.
"""
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render

from accounts.models import Role
from claims.models import Claim
from items.choices import Category, Place
from items.models import FoundItem

from .forms import SearchForm

# The only columns this page is allowed to read.
PUBLIC_FIELDS = ['id', 'category', 'description', 'place', 'date_found']


def codes_with_word(choices, word):
    """
    Finds the dropdown codes whose label contains a word.
    Example: the word "library" gives ['library'], because the place label is "Library".
    """
    codes = []
    for code, label in choices:
        if word in label.lower():
            codes.append(code)
    return codes


@login_required
def search_items(request):
    if request.user.role not in (Role.STUDENT, Role.STAFF):
        raise PermissionDenied

    # Start with every item still held at the security desk, public columns only.
    items = FoundItem.objects.filter(status=FoundItem.Status.IN_CUSTODY).only(*PUBLIC_FIELDS)

    form = SearchForm(request.GET or None)
    if form.is_valid():
        # 1. Every word typed must be in the description, the category or the place.
        for word in form.cleaned_data['q'].lower().split():
            if len(word) < 3:                 # skip short words like "a", "my", "in"
                continue
            # Q(...) | Q(...) means "this OR that"
            items = items.filter(Q(description__icontains=word)
                                 | Q(category__in=codes_with_word(Category.choices, word))
                                 | Q(place__in=codes_with_word(Place.choices, word)))
        # 2. The two dropdowns narrow the list further.
        if form.cleaned_data['category']:
            items = items.filter(category=form.cleaned_data['category'])
        if form.cleaned_data['place']:
            items = items.filter(place=form.cleaned_data['place'])

    # NFR-05: show 10 items on a page instead of everything at once.
    page = Paginator(items, 10).get_page(request.GET.get('page'))

    # Items this person has already claimed show "Claimed by you" instead of the Claim button.
    my_claimed_ids = list(Claim.objects.filter(user=request.user).values_list('found_item_id', flat=True))

    # Keep the search words in the Previous / Next links.
    query = request.GET.copy()
    query.pop('page', None)
    return render(request, 'search/search.html',
                  {'form': form, 'page': page, 'query': query.urlencode(), 'my_claimed_ids': my_claimed_ids})
