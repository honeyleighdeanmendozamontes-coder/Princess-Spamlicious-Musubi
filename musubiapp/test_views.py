from django.shortcuts import render
from django.conf import settings
from .models import Product

def test_images(request):
    """Test view to check image loading"""
    products = Product.objects.exclude(image='')
    
    context = {
        'products': products,
        'MEDIA_URL': settings.MEDIA_URL,
        'DEBUG': settings.DEBUG,
    }
    
    return render(request, 'musubiapp/test_images.html', context)
