from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    """
    home page

    Returns:
        HttpResponse: index page html
    """
    return render(request, 'index.html')

