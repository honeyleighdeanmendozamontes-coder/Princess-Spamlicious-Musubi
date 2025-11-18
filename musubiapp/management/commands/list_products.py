from django.core.management.base import BaseCommand
from musubiapp.models import Product

class Command(BaseCommand):
    help = 'List all products with their images'

    def handle(self, *args, **options):
        products = Product.objects.all()
        
        self.stdout.write(self.style.SUCCESS('Current Products:'))
        self.stdout.write('-' * 60)
        
        for product in products:
            image_status = "[HAS IMAGE]" if product.image else "[NO IMAGE]"
            self.stdout.write(f'ID: {product.id}')
            self.stdout.write(f'Name: {product.name}')
            self.stdout.write(f'Price: P{product.price}')
            self.stdout.write(f'Category: {product.category}')
            self.stdout.write(f'Stock: {product.stock}')
            self.stdout.write(f'Image: {product.image} {image_status}')
            self.stdout.write(f'Active: {product.is_active}')
            self.stdout.write('-' * 60)
