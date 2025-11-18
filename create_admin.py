from django.contrib.auth.models import User
from musubiapp.models import Customer, Cart

# Create admin user
username = 'admin'
email = 'admin@example.com'
password = 'admin123'

# Check if user already exists
if User.objects.filter(username=username).exists():
    print(f"User '{username}' already exists!")
    user = User.objects.get(username=username)
else:
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name='Admin',
        last_name='User'
    )
    print(f"Created user: {username}")

# Check if customer profile exists
if hasattr(user, 'customer'):
    print(f"Customer profile already exists for {username}")
    customer = user.customer
    # Update role to admin if needed
    if customer.role != 'admin':
        customer.role = 'admin'
        customer.save()
        print(f"Updated {username} role to admin")
else:
    # Create customer profile
    customer = Customer.objects.create(
        user=user,
        role='admin',
        phone='1234567890',
        address='Admin Address'
    )
    print(f"Created customer profile for {username} with admin role")

# Create cart if doesn't exist
if not Cart.objects.filter(customer=customer).exists():
    Cart.objects.create(customer=customer)
    print(f"Created cart for {username}")

print("\n✅ Admin account ready!")
print(f"Username: {username}")
print(f"Password: {password}")
print(f"Role: {customer.role}")
