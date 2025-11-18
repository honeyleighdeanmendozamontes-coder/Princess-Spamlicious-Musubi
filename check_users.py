import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'musubiproject.settings')
django.setup()

from musubiapp.models import Customer
from django.contrib.auth.models import User

print("=== USER ROLES CHECK ===\n")
users = User.objects.all()
for user in users:
    has_customer = hasattr(user, 'customer')
    role = user.customer.role if has_customer else "N/A"
    print(f"Username: {user.username}")
    print(f"  - Has Customer Profile: {has_customer}")
    print(f"  - Role: {role}")
    print(f"  - Can access cart: {has_customer and role == 'customer'}")
    print()
