from django.core.management.base import BaseCommand
from musubiapp.models import Product
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Test media file accessibility'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing Media Configuration:'))
        self.stdout.write('-' * 50)
        
        # Check settings
        self.stdout.write(f'DEBUG: {settings.DEBUG}')
        self.stdout.write(f'MEDIA_URL: {settings.MEDIA_URL}')
        self.stdout.write(f'MEDIA_ROOT: {settings.MEDIA_ROOT}')
        self.stdout.write('-' * 50)
        
        # Check products with images
        products_with_images = Product.objects.exclude(image='')
        
        self.stdout.write(f'Products with images: {products_with_images.count()}')
        self.stdout.write('-' * 50)
        
        for product in products_with_images:
            image_path = os.path.join(settings.MEDIA_ROOT, str(product.image))
            file_exists = os.path.exists(image_path)
            
            self.stdout.write(f'Product: {product.name}')
            self.stdout.write(f'Image field: {product.image}')
            self.stdout.write(f'Full path: {image_path}')
            self.stdout.write(f'File exists: {file_exists}')
            self.stdout.write(f'Expected URL: {settings.MEDIA_URL}{product.image}')
            self.stdout.write('-' * 30)
        
        self.stdout.write(self.style.SUCCESS('Media test completed!'))
