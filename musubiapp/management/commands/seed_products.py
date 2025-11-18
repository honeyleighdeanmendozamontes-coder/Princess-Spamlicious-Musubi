# Create this file: musubiapp/management/commands/seed_products.py
from django.core.management.base import BaseCommand
from musubiapp.models import Product

class Command(BaseCommand):
    help = 'Seed the database with sample products'

    def handle(self, *args, **options):
        products = [
            {
                'name': 'Classic Spam Musubi',
                'description': 'Grilled Spam wrapped with nori on seasoned rice. The authentic Hawaiian favorite!',
                'price': 45.00,
                'category': 'classic',
                'stock': 50,
                'is_featured': True
            },
            {
                'name': 'Spam & Egg Musubi', 
                'description': 'Classic Spam Musubi with a fluffy egg layer. Perfect breakfast option!',
                'price': 55.00,
                'category': 'classic',
                'stock': 30,
                'is_featured': True
            },
            {
                'name': 'Chicken Teriyaki Musubi',
                'description': 'Grilled chicken with sweet teriyaki sauce on seasoned rice. A customer favorite!',
                'price': 60.00, 
                'category': 'special',
                'stock': 25,
                'is_featured': True
            },
            {
                'name': '5-Piece Musubi Box',
                'description': 'Perfect for sharing! Includes 3 Classic Spam and 2 Spam & Egg Musubi.',
                'price': 200.00,
                'bundle_price': 180.00,
                'category': 'combo', 
                'stock': 15,
                'is_featured': False
            },
            {
                'name': 'Tuna Musubi',
                'description': 'Fresh tuna with mayonnaise and seasonings. A lighter option!',
                'price': 50.00,
                'category': 'special',
                'stock': 20,
                'is_featured': False
            },
            {
                'name': 'Family Pack (10 pcs)',
                'description': 'Great for parties! 10 assorted musubi with your choice of varieties.',
                'price': 450.00,
                'bundle_price': 400.00,
                'category': 'combo',
                'stock': 10,
                'is_featured': True
            }
        ]

        for product_data in products:
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                defaults=product_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created: {product.name} - ₱{product.price}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'📦 Already exists: {product.name}')
                )