from django.conf import settings
from django.http import Http404
from django.shortcuts import render


def landing(request):
    return render(request, "base.html")


def styleguide(request):
    if not settings.DEBUG:
        raise Http404("Styleguide is only available in DEBUG mode.")
    return render(request, "site_pages/styleguide.html")
