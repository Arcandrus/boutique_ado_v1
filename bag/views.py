from django.shortcuts import render

# Create your views here.

def view_bag(request):
    """ Return shopping bag main page """
    return render(request, 'bag/bag.html')