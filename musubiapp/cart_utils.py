from django.conf import settings
from .models import Product

def get_cart(request):
    """Get the cart from session or create empty one"""
    cart = request.session.get(settings.CART_SESSION_ID)
    if not cart:
        cart = request.session[settings.CART_SESSION_ID] = {}
    return cart

def get_cart_items(request):
    """Get cart items with product objects"""
    cart = get_cart(request)
    cart_items = []
    
    for product_id, item_data in cart.items():
        try:
            product = Product.objects.get(id=product_id, available=True)
            cart_items.append({
                'product': product,
                'quantity': item_data['quantity'],
                'total_price': product.price * item_data['quantity']
            })
        except Product.DoesNotExist:
            # Remove invalid products from cart
            del cart[product_id]
            request.session.modified = True
    
    return cart_items

def add_to_cart(request, product_id, quantity=1):
    """Add product to cart or update quantity"""
    cart = get_cart(request)
    
    product_id = str(product_id)
    
    if product_id in cart:
        cart[product_id]['quantity'] += quantity
    else:
        cart[product_id] = {'quantity': quantity}
    
    request.session.modified = True

def remove_from_cart(request, product_id):
    """Remove product from cart"""
    cart = get_cart(request)
    product_id = str(product_id)
    
    if product_id in cart:
        del cart[product_id]
        request.session.modified = True

def update_cart_quantity(request, product_id, quantity):
    """Update product quantity in cart"""
    cart = get_cart(request)
    product_id = str(product_id)
    
    if quantity <= 0:
        remove_from_cart(request, product_id)
    elif product_id in cart:
        cart[product_id]['quantity'] = quantity
        request.session.modified = True

def clear_cart(request):
    """Clear all items from cart"""
    if settings.CART_SESSION_ID in request.session:
        del request.session[settings.CART_SESSION_ID]
        request.session.modified = True

def get_cart_total(request):
    """Calculate total price of all items in cart"""
    cart_items = get_cart_items(request)
    return sum(item['total_price'] for item in cart_items)

def get_cart_item_count(request):
    """Get total number of items in cart"""
    cart = get_cart(request)
    return sum(item['quantity'] for item in cart.values())