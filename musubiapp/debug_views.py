from django.http import JsonResponse
from django.conf import settings
from musubiapp.models import Product
import os

def debug_media(request):
    """Debug view to check media configuration"""
    
    # Get products with images
    products = Product.objects.exclude(image='')
    
    debug_info = {
        'settings': {
            'DEBUG': settings.DEBUG,
            'MEDIA_URL': settings.MEDIA_URL,
            'MEDIA_ROOT': str(settings.MEDIA_ROOT),
        },
        'products': []
    }
    
    for product in products:
        image_path = os.path.join(settings.MEDIA_ROOT, str(product.image))
        debug_info['products'].append({
            'id': product.id,
            'name': product.name,
            'image_field': str(product.image),
            'image_url': f"{settings.MEDIA_URL}{product.image}",
            'full_path': image_path,
            'file_exists': os.path.exists(image_path),
            'file_size': os.path.getsize(image_path) if os.path.exists(image_path) else 0
        })
    
    return JsonResponse(debug_info, indent=2)
