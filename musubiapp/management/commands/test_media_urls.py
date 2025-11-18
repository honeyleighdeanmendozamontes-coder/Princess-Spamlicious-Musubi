from django.core.management.base import BaseCommand
from django.test import Client
from django.conf import settings
from musubiapp.models import Product

class Command(BaseCommand):
    help = 'Test media URL accessibility'

    def handle(self, *args, **options):
        client = Client()
        
        self.stdout.write(self.style.SUCCESS('Testing Media URLs:'))
        self.stdout.write('-' * 50)
        
        # Test direct media URLs
        test_urls = [
            '/media/products/classic_spam_musubi.jpg',
            '/media/products/spam_egg_musubi.jpg',
            '/media/products/spam_musubi.jpg',
        ]
        
        for url in test_urls:
            try:
                response = client.get(url)
                status = response.status_code
                content_type = response.get('Content-Type', 'unknown')
                
                self.stdout.write(f'URL: {url}')
                self.stdout.write(f'Status: {status}')
                self.stdout.write(f'Content-Type: {content_type}')
                
                if status == 200:
                    self.stdout.write(self.style.SUCCESS('✓ SUCCESS'))
                else:
                    self.stdout.write(self.style.ERROR('✗ FAILED'))
                    
                self.stdout.write('-' * 30)
                
            except Exception as e:
                self.stdout.write(f'URL: {url}')
                self.stdout.write(self.style.ERROR(f'ERROR: {str(e)}'))
                self.stdout.write('-' * 30)
        
        # Test product image URLs
        self.stdout.write('Testing Product Image URLs:')
        products_with_images = Product.objects.exclude(image='')
        
        for product in products_with_images:
            image_url = f'/media/{product.image}'
            try:
                response = client.get(image_url)
                status = response.status_code
                
                self.stdout.write(f'Product: {product.name}')
                self.stdout.write(f'Image URL: {image_url}')
                self.stdout.write(f'Status: {status}')
                
                if status == 200:
                    self.stdout.write(self.style.SUCCESS('✓ SUCCESS'))
                else:
                    self.stdout.write(self.style.ERROR('✗ FAILED'))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'ERROR: {str(e)}'))
                
            self.stdout.write('-' * 30)
        
        self.stdout.write(self.style.SUCCESS('Media URL test completed!'))
