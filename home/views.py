from django.shortcuts import render

# Create your views here.


def index(request):
    """Return index.html page"""
    return render(request, "home/index.html")
