# musubiapp/management/commands/update_menu.py
from django.core.management.base import BaseCommand
from musubiapp.models import Product

class Command(BaseCommand):
    help = 'Update menu with new products'

    def handle(self, *args, **kwargs):
        # Delete all existing products
        Product.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Deleted all existing products'))

        # Create new products
        products = [
            {
                'name': 'With Egg Spam Musubi',
                'description': 'Delicious spam musubi with egg - a perfect combination of savory spam and fluffy egg wrapped in rice and nori.',
                'price': 55.00,
                'stock': 50,
                'category': 'spam',
                'is_active': True,
            },
            {
                'name': 'No Egg Spam Musubi',
                'description': 'Classic spam musubi without egg - simple and delicious with perfectly grilled spam on seasoned rice.',
                'price': 45.00,
                'stock': 50,
                'category': 'spam',
                'is_active': True,
            },
            {
                'name': 'Hawaiian With Egg Musubi',
                'description': 'Hawaiian-style musubi with egg - featuring sweet and savory teriyaki-glazed spam with egg, pineapple flavor, and premium ingredients.',
                'price': 60.00,
                'stock': 50,
                'category': 'special',
                'is_active': True,
            },
        ]

        for product_data in products:
            product = Product.objects.create(**product_data)
            self.stdout.write(self.style.SUCCESS(f'Created product: {product.name} - ₱{product.price}'))

        self.stdout.write(self.style.SUCCESS('\n✅ Menu updated successfully!'))
        self.stdout.write(self.style.SUCCESS('New menu items:'))
        self.stdout.write(self.style.SUCCESS('  1. With Egg Spam Musubi - ₱55'))
        self.stdout.write(self.style.SUCCESS('  2. No Egg Spam Musubi - ₱45'))
        self.stdout.write(self.style.SUCCESS('  3. Hawaiian With Egg Musubi - ₱60'))
