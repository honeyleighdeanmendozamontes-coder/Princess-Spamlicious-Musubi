from django.core.management.base import BaseCommand
from musubiapp.models import Product
import os

class Command(BaseCommand):
    help = 'Update product images for musubi products'

    def handle(self, *args, **options):
        # Image mappings based on the uploaded images
        image_mappings = {
            'Spam Musubi': 'products/classic_spam_musubi.jpg',
            'Classic Spam Musubi': 'products/classic_spam_musubi.jpg',
            'Spam & Egg Musubi': 'products/spam_egg_musubi.jpg',
            'Teriyaki Spam Musubi': 'products/spam_musubi.jpg',
        }
        
        # Update existing products or create them if they don't exist
        products_data = [
            {
                'name': 'Classic Spam Musubi',
                'description': 'Traditional spam musubi with perfectly seasoned rice and grilled spam wrapped in nori seaweed.',
                'price': 60.00,
                'category': 'spam',
                'image': 'products/classic_spam_musubi.jpg',
                'stock': 50
            },
            {
                'name': 'Spam & Egg Musubi',
                'description': 'Delicious spam musubi with fluffy scrambled egg, rice, and nori seaweed for extra flavor.',
                'price': 75.00,
                'category': 'spam',
                'image': 'products/spam_egg_musubi.jpg',
                'stock': 40
            },
            {
                'name': 'Teriyaki Spam Musubi',
                'description': 'Grilled spam glazed with sweet teriyaki sauce, served on seasoned rice with nori wrap.',
                'price': 70.00,
                'category': 'spam',
                'image': 'products/spam_musubi.jpg',
                'stock': 45
            }
        ]
        
        updated_count = 0
        created_count = 0
        
        for product_data in products_data:
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                defaults=product_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created product: {product.name}')
                )
            else:
                # Update existing product with new image and other details
                product.description = product_data['description']
                product.price = product_data['price']
                product.category = product_data['category']
                product.image = product_data['image']
                product.stock = product_data['stock']
                product.is_active = True
                product.save()
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Updated product: {product.name}')
                )
        
        # Try to update any existing products that match the image mappings
        for product_name, image_path in image_mappings.items():
            try:
                products = Product.objects.filter(name__icontains=product_name.split()[0])
                for product in products:
                    if not product.image:
                        product.image = image_path
                        product.save()
                        updated_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'Added image to existing product: {product.name}')
                        )
            except Product.DoesNotExist:
                pass
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {updated_count} products and created {created_count} new products with images!'
            )
        )
