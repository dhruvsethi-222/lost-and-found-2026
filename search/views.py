"""
Search found items (ST-P5, SF-P5) and show the results (ST-O2, SF-O2).

Privacy (NFR-02): this code only ever reads the public columns of found_item.
It never touches verification_detail, so serial numbers, marks and contents
cannot appear on this page, whatever is typed.
"""
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render

from accounts.decorators import student_or_staff
from items.choices import Category, Place
from items.models import FoundItem

from .forms import SearchForm

PUBLIC_FIELDS = ('id', 'category', 'description', 'place', 'date_found')


def codes_matching(choices, word):
    """Which category or place codes have this word in their label? e.g. 'wallet' -> ['wallet']."""
    return [code for code, label in choices if word in label.lower()]


@student_or_staff
def search_items(request):
    form = SearchForm(request.GET or None)
    items = FoundItem.objects.filter(status=FoundItem.Status.IN_CUSTODY).only(*PUBLIC_FIELDS)
    if form.is_valid():
        # every word typed must match the description, the category or the place
        for word in form.cleaned_data['q'].lower().split():
            if len(word) < 3:                    # skip words like "a", "my", "in"
                continue
            items = items.filter(Q(description__icontains=word)
                                 | Q(category__in=codes_matching(Category.choices, word))
                                 | Q(place__in=codes_matching(Place.choices, word)))
        if form.cleaned_data['category']:
            items = items.filter(category=form.cleaned_data['category'])
        if form.cleaned_data['place']:
            items = items.filter(place=form.cleaned_data['place'])
    page = Paginator(items, 10).get_page(request.GET.get('page'))     # 10 per page (NFR-05)
    query = request.GET.copy()
    query.pop('page', None)
    return render(request, 'search/search.html', {'form': form, 'page': page, 'query': query.urlencode()})
