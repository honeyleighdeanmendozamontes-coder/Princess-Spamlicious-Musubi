# musubiapp/management/commands/setup_initial_data.py
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from musubiapp.models import Customer, Product

class Command(BaseCommand):
    help = 'Create initial admin user and sample products'

    def handle(self, *args, **options):
        # Create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@spamlicious.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Created admin user'))

        # Create admin customer profile
        admin_customer, created = Customer.objects.get_or_create(
            user=admin_user,
            defaults={'role': 'admin'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created admin customer profile'))

        # Create sample staff user
        staff_user, created = User.objects.get_or_create(
            username='staff',
            defaults={
                'email': 'staff@spamlicious.com',
                'is_staff': True
            }
        )
        if created:
            staff_user.set_password('staff123')
            staff_user.save()
            self.stdout.write(self.style.SUCCESS('Created staff user'))

        staff_customer, created = Customer.objects.get_or_create(
            user=staff_user,
            defaults={'role': 'staff'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created staff customer profile'))

        # Create sample products
        sample_products = [
            {
                'name': 'Classic Spam Musubi',
                'description': 'Traditional Hawaiian spam musubi with our special sauce',
                'price': 65.00,
                'bundle_price': 300.00,
                'stock': 50,
                'category': 'spam'
            },
            {
                'name': 'Teriyaki Chicken Musubi',
                'description': 'Grilled chicken with teriyaki glaze wrapped in rice and nori',
                'price': 75.00,
                'bundle_price': 350.00,
                'stock': 30,
                'category': 'chicken'
            },
            {
                'name': 'Vegetarian Tofu Musubi',
                'description': 'Marinated tofu with fresh vegetables - perfect for vegetarians',
                'price': 70.00,
                'bundle_price': 320.00,
                'stock': 25,
                'category': 'vegetarian'
            },
            {
                'name': 'Special Hawaiian Musubi',
                'description': 'Our signature musubi with special ingredients and sauce',
                'price': 85.00,
                'bundle_price': 400.00,
                'stock': 20,
                'category': 'special'
            },
        ]

        for product_data in sample_products:
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                defaults=product_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created product: {product.name}'))

        self.stdout.write(
            self.style.SUCCESS('Successfully created all initial data!')
        )
        self.stdout.write(
            self.style.SUCCESS('Demo accounts:')
        )
        self.stdout.write(
            self.style.SUCCESS('Admin: username=admin, password=admin123')
        )
        self.stdout.write(
            self.style.SUCCESS('Staff: username=staff, password=staff123')
        )