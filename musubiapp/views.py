# musubiapp/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Customer, Product, Cart, CartItem, Order, OrderItem, InventoryLog, Reservation, ReservationItem, Message, Notification, ActivityLog, Review, Feedback
from .utils import log_activity
from django.db import transaction
from django.db.models import Sum, Count, Avg, Q
from datetime import date, timedelta
from django.utils import timezone
from django.db import models
from decimal import Decimal
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.tokens import default_token_generator
import json
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from .debug_views import debug_media
from .test_views import test_images
import os

# Role-based access decorators - MOVED TO TOP
def customer_required(function=None):
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and hasattr(u, 'customer') and u.customer.role == 'customer',
        login_url='customer_login'
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def staff_required(function=None):
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and hasattr(u, 'customer') and u.customer.role in ['staff', 'admin'],
        login_url='customer_login'
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def admin_required(function=None):
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and hasattr(u, 'customer') and u.customer.role == 'admin',
        login_url='customer_login'
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

# Authentication Views
def customer_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            # Support login by email or username
            login_username = username_or_email
            if username_or_email and '@' in username_or_email:
                try:
                    from django.contrib.auth.models import User
                    u = User.objects.get(email=username_or_email)
                    login_username = u.username
                except User.DoesNotExist:
                    login_username = username_or_email  # will fail auth normally

            user = authenticate(username=login_username, password=password)
            
            if user is not None:
                # Allow superusers/staff to log in even without a Customer profile
                if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
                    login(request, user)
                    log_activity(
                        user=user,
                        action='login',
                        entity_type='system',
                        description=f'Admin/staff {user.username} logged in',
                        request=request
                    )
                    return redirect('admin_dashboard')

                # Otherwise, require a Customer profile for normal users
                try:
                    customer = Customer.objects.get(user=user)
                    login(request, user)
                    
                    # Log login activity
                    log_activity(
                        user=user,
                        action='login',
                        entity_type='system',
                        description=f'User {user.username} logged in',
                        request=request
                    )
                    
                    # Redirect based on role
                    if customer.role == 'admin':
                        return redirect('admin_dashboard')
                    else:
                        return redirect('product_list')  # Redirect customers to menu
                        
                except Customer.DoesNotExist:
                    messages.error(request, 'No customer profile found.')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'musubiapp/login.html')

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        
        # Basic validation
        if not username or not email or not password:
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'musubiapp/register.html')
            
        if password != password_confirm:
            messages.error(request, "Passwords don't match.")
            return render(request, 'musubiapp/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, 'musubiapp/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return render(request, 'musubiapp/register.html')
        
        try:
            with transaction.atomic():
                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name or '',
                    last_name=last_name or ''
                )
                
                # Create customer profile
                customer = Customer.objects.create(
                    user=user,
                    role='customer',
                    phone=phone or '',
                    address=address or ''
                )
                
                # Create cart for customer
                Cart.objects.create(customer=customer)
                
                # Log registration activity
                log_activity(
                    user=user,
                    action='create',
                    entity_type='customer',
                    entity_id=customer.id,
                    description=f'New customer registered: {username}',
                    request=request
                )
                
                messages.success(request, "Account created successfully! Please login.")
                return redirect('customer_login')
                
        except Exception as e:
            messages.error(request, f"Error creating account: {str(e)}")
            return render(request, 'musubiapp/register.html')
    
    # If GET request, show the registration form
    return render(request, 'musubiapp/register.html')

@csrf_exempt
def custom_logout(request):
    """Handle logout for both GET and POST requests"""
    # Log logout activity before logging out
    if request.user.is_authenticated:
        log_activity(
            user=request.user,
            action='logout',
            entity_type='system',
            description=f'User {request.user.username} logged out',
            request=request
        )
    
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('home')

# Password Reset Views
def forgot_password(request):
    """Handle forgot password request"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = User.objects.get(email=email)
            
            # Generate password reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Build reset link
            reset_link = request.build_absolute_uri(
                f'/reset-password/{uid}/{token}/'
            )
            
            # Send email (for now, we'll just show the link in console)
            # In production, configure email settings to send actual emails
            subject = 'Password Reset Request - Spamlicious Musubi'
            message = f'''
Hello {user.username},

You requested to reset your password for your Spamlicious Musubi account.

Click the link below to reset your password:
{reset_link}

This link will expire in 24 hours.

If you didn't request this, please ignore this email.

Best regards,
Spamlicious Musubi Team
            '''
            
            try:
                # Try to send email
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@spamlicious.com',
                    [email],
                    fail_silently=False,
                )
                messages.success(request, 'Password reset link has been sent to your email.')
            except Exception as e:
                # If email fails, show the link directly (for development)
                print(f"Email sending failed: {e}")
                print(f"Reset link: {reset_link}")
                messages.success(request, f'Password reset link: {reset_link}')
            
            # Log activity
            log_activity(
                user=user,
                action='view',
                entity_type='system',
                description=f'Password reset requested for {user.username}',
                request=request
            )
            
            return redirect('customer_login')
            
        except User.DoesNotExist:
            messages.error(request, 'No account found with that email address.')
    
    return render(request, 'musubiapp/forgot_password.html')

def reset_password(request, uidb64, token):
    """Handle password reset with token"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')
            
            if password != password_confirm:
                messages.error(request, "Passwords don't match.")
                return render(request, 'musubiapp/reset_password.html', {'validlink': True})
            
            if len(password) < 8:
                messages.error(request, "Password must be at least 8 characters long.")
                return render(request, 'musubiapp/reset_password.html', {'validlink': True})
            
            # Set new password
            user.set_password(password)
            user.save()
            
            # Log activity
            log_activity(
                user=user,
                action='update',
                entity_type='system',
                description=f'Password reset completed for {user.username}',
                request=request
            )
            
            messages.success(request, 'Your password has been reset successfully. Please login with your new password.')
            return redirect('customer_login')
        
        return render(request, 'musubiapp/reset_password.html', {'validlink': True})
    else:
        messages.error(request, 'Invalid or expired password reset link.')
        return render(request, 'musubiapp/reset_password.html', {'validlink': False})

# Public Views
def home(request):
    """Home page - accessible to all users"""
    featured_products = Product.objects.filter(is_active=True, stock__gt=0)[:6]
    return render(request, 'musubiapp/home.html', {
        'featured_products': featured_products
    })

@login_required
def product_list(request):
    products = Product.objects.filter(is_active=True).annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews', filter=models.Q(reviews__is_approved=True))
    )
    return render(request, 'musubiapp/product_list.html', {
        'products': products
    })

@login_required
def product_detail(request, product_id):
    try:
        product = Product.objects.get(id=product_id, is_active=True)
        reviews = Review.objects.filter(product=product, is_approved=True).select_related('customer__user').order_by('-created_at')
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
        review_count = reviews.count()
        
        # Check if current user has purchased this product
        customer = request.user.customer
        has_purchased = OrderItem.objects.filter(
            order__customer=customer,
            product=product,
            order__status='completed'
        ).exists()
        
        # Check if user already reviewed
        user_review = Review.objects.filter(product=product, customer=customer).first()
        
        return render(request, 'musubiapp/product_detail.html', {
            'product': product,
            'reviews': reviews,
            'avg_rating': avg_rating,
            'review_count': review_count,
            'has_purchased': has_purchased,
            'user_review': user_review
        })
    except Product.DoesNotExist:
        messages.error(request, 'Product not found.')
        return redirect('product_list')

# Customer Views
@customer_required
def add_to_cart(request, product_id):
    if request.method == 'POST':
        try:
            product = Product.objects.get(id=product_id, is_active=True, stock__gt=0)
            cart, created = Cart.objects.get_or_create(customer=request.user.customer)
            
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': 1}
            )
            
            if not created:
                cart_item.quantity += 1
                cart_item.save()
            
            # Get updated cart count
            cart_count = CartItem.objects.filter(cart=cart).count()
            
            return JsonResponse({
                'success': True,
                'message': 'Product added to cart!',
                'cart_count': cart_count
            })
            
        except Product.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Product not available'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@customer_required
def view_cart(request):
    customer = request.user.customer
    cart, created = Cart.objects.get_or_create(customer=customer)
    cart_items = CartItem.objects.filter(cart=cart)
    total = sum(item.get_total() for item in cart_items)
    
    return render(request, 'musubiapp/cart.html', {
        'cart_items': cart_items,
        'total': total,
        'customer_address': customer.address or ''
    })

@customer_required
def update_cart(request, cart_item_id):
    if request.method == 'POST':
        try:
            cart_item = CartItem.objects.get(id=cart_item_id, cart__customer=request.user.customer)
            action = request.POST.get('action')
            
            if action == 'update':
                quantity = int(request.POST.get('quantity', 1))
                if quantity > 0:
                    cart_item.quantity = quantity
                    cart_item.save()
                else:
                    cart_item.delete()
            elif action == 'remove':
                cart_item.delete()
                
            messages.success(request, 'Cart updated successfully!')
        except CartItem.DoesNotExist:
            messages.error(request, 'Cart item not found.')
    
    return redirect('view_cart')

@customer_required
def clear_cart(request):
    if request.method == 'POST':
        cart = Cart.objects.get(customer=request.user.customer)
        CartItem.objects.filter(cart=cart).delete()
        messages.success(request, 'Cart cleared successfully!')
    
    return redirect('view_cart')

@customer_required
def checkout(request):
    try:
        customer = request.user.customer
        cart = Cart.objects.get(customer=customer)
        cart_items = CartItem.objects.filter(cart=cart)
        
        if not cart_items:
            messages.error(request, "Your cart is empty!")
            return redirect('view_cart')
        
        # Calculate subtotal
        subtotal = sum(item.get_total() for item in cart_items)
        delivery_fee = Decimal('50.00')
        
        # First-time customer discount: 10% of subtotal, capped at ₱200
        discount_amount = Decimal('0.00')
        discount_details = ''
        from .models import Order  # local import to avoid circular issues
        is_first_order = not Order.objects.filter(customer=request.user.customer, status='completed').exists()
        
        if is_first_order and subtotal > 0:
            raw_discount = (subtotal * Decimal('0.10')).quantize(Decimal('0.01'))
            discount_cap = Decimal('200.00')
            discount_amount = raw_discount if raw_discount <= discount_cap else discount_cap
            discount_details = 'First-time order 10% discount (max ₱200)'
        
        grand_total = subtotal + delivery_fee - discount_amount
        
        if request.method == 'POST':
            # Process the order
            delivery_address = request.POST.get('delivery_address') or (customer.address or '')
            notes = request.POST.get('notes', '')
            payment_method = request.POST.get('payment_method', 'cod')  # Default to COD
            
            # Create order
            order = Order.objects.create(
                customer=request.user.customer,
                total_amount=grand_total,
                discount_amount=discount_amount,
                discount_details=discount_details,
                delivery_address=delivery_address,
                notes=notes,
                payment_method=payment_method,
                payment_status='pending'  # COD payment is pending until delivery
            )
            
            # Create order items and update inventory
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price
                )
                
                # Update product stock
                cart_item.product.stock -= cart_item.quantity
                cart_item.product.save()
                
                # Log inventory change
                InventoryLog.objects.create(
                    product=cart_item.product,
                    action='sold',
                    quantity=cart_item.quantity,
                    previous_stock=cart_item.product.stock + cart_item.quantity,
                    new_stock=cart_item.product.stock,
                    notes=f"Sold via order #{order.id}",
                    created_by=request.user
                )
            
            # Clear the cart
            cart_items.delete()
            
            # Create notification for all admins about new order
            admin_users = User.objects.filter(customer__role='admin')
            for admin_user in admin_users:
                Notification.objects.create(
                    user=admin_user,
                    notification_type='new_order',
                    title='New Order Received',
                    message=f'New order #{order.id} from {request.user.username}. Total: ₱{order.total_amount}',
                    order=order
                )
            
            # Log order creation activity
            log_activity(
                user=request.user,
                action='create',
                entity_type='order',
                entity_id=order.id,
                description=f'Customer placed order #{order.id} - Total: ₱{order.total_amount}',
                request=request
            )
            
            messages.success(request, f"Order placed successfully! Order #{order.id} - Payment: Cash on Delivery. Please have the exact amount (₱{order.total_amount}) ready when your order arrives.")
            return redirect('home')
        
        return render(request, 'musubiapp/checkout.html', {
            'cart_items': cart_items,
            'subtotal': subtotal,
            'discount_amount': discount_amount,
            'delivery_fee': delivery_fee,
            'grand_total': grand_total,
            'is_first_time_discount_applied': is_first_order,
            'customer_address': customer.address or ''
        })
        
    except Cart.DoesNotExist:
        messages.error(request, "Cart not found!")
        return redirect('home')

@login_required
def profile_view(request):
    user = request.user
    customer = user.customer
    
    # Check if user is admin and render admin profile template
    if customer.role == 'admin':
        # Get admin statistics
        total_orders = Order.objects.count()
        total_customers = Customer.objects.filter(role='customer').count()
        total_products = Product.objects.filter(is_active=True).count()
        pending_orders = Order.objects.filter(status='pending').count()
        
        # Get unread notifications count
        unread_notifications_count = Notification.objects.filter(
            user=user,
            is_read=False
        ).count()
        
        return render(request, 'musubiapp/admin_profile.html', {
            'user': user,
            'customer': customer,
            'total_orders': total_orders,
            'total_customers': total_customers,
            'total_products': total_products,
            'pending_orders': pending_orders,
            'unread_notifications_count': unread_notifications_count,
        })
    
    # For regular customers, show customer profile
    # Get user's orders
    orders = Order.objects.filter(customer=customer).order_by('-created_at')
    
    # Calculate statistics
    total_orders = orders.count()
    completed_orders = orders.filter(status='completed').count()
    pending_orders = orders.filter(status='pending').count()
    total_spent = orders.filter(status='completed').aggregate(total=Sum('total_amount'))['total'] or 0
    
    return render(request, 'musubiapp/profile.html', {
        'user': user,
        'customer': customer,
        'orders': orders,
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'pending_orders': pending_orders,
    })

@login_required
def edit_profile(request):
    """Edit customer profile"""
    customer = request.user.customer
    
    if request.method == 'POST':
        # Update user info
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        
        # Update customer info
        customer.phone = request.POST.get('phone', '')
        customer.address = request.POST.get('address', '')
        
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            customer.profile_picture = request.FILES['profile_picture']
        
        customer.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    return render(request, 'musubiapp/edit_profile.html', {
        'user': request.user,
        'customer': customer
    })

@customer_required
def update_address(request):
    """AJAX endpoint to update customer address"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            new_address = data.get('address', '').strip()
            
            if new_address:
                customer = request.user.customer
                customer.address = new_address
                customer.save()
                
                return JsonResponse({'success': True, 'message': 'Address updated successfully'})
            else:
                return JsonResponse({'success': False, 'message': 'Address cannot be empty'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def change_password(request):
    """Change customer password"""
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Check if new passwords match
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match!')
            return redirect('change_password')
        
        # Check password length
        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long!')
            return redirect('change_password')
        
        # Update password
        request.user.set_password(new_password)
        request.user.save()
        
        # Update session to prevent logout
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, request.user)
        
        messages.success(request, 'Password changed successfully!')
        return redirect('profile')
    
    return render(request, 'musubiapp/change_password.html')

# Customer Reservation Views
@customer_required
def customer_reservations(request):
    """View customer's reservations"""
    customer = request.user.customer
    reservations = Reservation.objects.filter(customer=customer).order_by('-reservation_date', '-reservation_time')
    
    return render(request, 'musubiapp/customer_reservations.html', {
        'reservations': reservations
    })

@customer_required
def customer_reservation_create(request):
    """Create a new reservation"""
    if request.method == 'POST':
        try:
            from datetime import date, timedelta
            
            reservation_date = request.POST.get('reservation_date')
            reservation_time = request.POST.get('reservation_time')
            number_of_guests = request.POST.get('number_of_guests')
            special_requests = request.POST.get('special_requests', '')
            delivery_address = request.POST.get('delivery_address', '')
            
            # Validate date restrictions
            selected_date = date.fromisoformat(reservation_date)
            today = date.today()
            max_date = today + timedelta(days=30)
            
            if selected_date < today:
                messages.error(request, 'Reservation date cannot be in the past.')
                raise ValueError('Invalid date')
            
            if selected_date > max_date:
                messages.error(request, 'Reservations can only be made up to 30 days in advance.')
                raise ValueError('Invalid date')
            
            reservation = Reservation.objects.create(
                customer=request.user.customer,
                reservation_date=reservation_date,
                reservation_time=reservation_time,
                number_of_guests=number_of_guests,
                special_requests=special_requests,
                delivery_address=delivery_address,
                status='pending'
            )
            
            # Handle product selections
            total_amount = 0
            products_ordered = []
            
            for key, value in request.POST.items():
                if key.startswith('product_') and value and int(value) > 0:
                    product_id = key.replace('product_', '')
                    quantity = int(value)
                    
                    try:
                        product = Product.objects.get(id=product_id)
                        if product.stock >= quantity:
                            ReservationItem.objects.create(
                                reservation=reservation,
                                product=product,
                                quantity=quantity,
                                price=product.price
                            )
                            total_amount += quantity * product.price
                            products_ordered.append(f"{product.name} x{quantity}")
                        else:
                            messages.warning(request, f'Insufficient stock for {product.name}. Only {product.stock} available.')
                    except Product.DoesNotExist:
                        continue
            
            # Log reservation creation activity
            products_info = ', '.join(products_ordered) if products_ordered else 'No products pre-ordered'
            log_activity(
                user=request.user,
                action='create',
                entity_type='reservation',
                entity_id=reservation.id,
                description=f'Customer created reservation #{reservation.id} for {reservation_date} at {reservation_time} - {products_info}',
                request=request
            )
            
            # Notify all admins about new reservation
            admin_users = User.objects.filter(customer__role='admin')
            notification_message = f'New reservation from {request.user.username} for {reservation_date} at {reservation_time} - {number_of_guests} guests'
            if total_amount > 0:
                notification_message += f' - Pre-order total: ₱{total_amount:.2f}'
            
            for admin_user in admin_users:
                Notification.objects.create(
                    user=admin_user,
                    notification_type='new_reservation',
                    title='New Reservation',
                    message=notification_message,
                    reservation=reservation
                )
            
            success_message = f'Reservation created successfully! Reservation #{reservation.id}'
            if total_amount > 0:
                success_message += f' with pre-order total of ₱{total_amount:.2f}'
            
            messages.success(request, success_message)
            return redirect('customer_reservations')
            
        except Exception as e:
            messages.error(request, f'Error creating reservation: {str(e)}')
    
    # Get available products for the form
    products = Product.objects.filter(stock__gt=0).order_by('name')
    products_json = json.dumps([{
        'id': p.id,
        'name': p.name,
        'price': str(p.price),
        'stock': p.stock
    } for p in products])
    
    return render(request, 'musubiapp/customer_reservation_form.html', {
        'form_title': 'Make a Reservation',
        'products': products,
        'products_json': products_json
    })

@customer_required
def customer_reservation_detail(request, reservation_id):
    """View reservation details"""
    customer = request.user.customer
    reservation = get_object_or_404(Reservation, id=reservation_id, customer=customer)
    
    return render(request, 'musubiapp/customer_reservation_detail.html', {
        'reservation': reservation
    })

@customer_required
def customer_reservation_cancel(request, reservation_id):
    """Cancel a reservation"""
    customer = request.user.customer
    reservation = get_object_or_404(Reservation, id=reservation_id, customer=customer)
    
    if request.method == 'POST':
        if reservation.status in ['pending', 'confirmed']:
            old_status = reservation.status
            reservation.status = 'cancelled'
            reservation.save()
            
            # Log reservation cancellation activity
            log_activity(
                user=request.user,
                action='update',
                entity_type='reservation',
                entity_id=reservation.id,
                description=f'Customer cancelled reservation #{reservation.id} (was {old_status})',
                request=request
            )
            
            messages.success(request, f'Reservation #{reservation.id} has been cancelled.')
        else:
            messages.error(request, 'This reservation cannot be cancelled.')
        
        return redirect('customer_reservations')
    
    return render(request, 'musubiapp/customer_reservation_cancel.html', {
        'reservation': reservation
    })

# Admin CRUD Views
@admin_required
def admin_dashboard(request):
    total_products = Product.objects.count()
    out_of_stock = Product.objects.filter(stock=0).count()
    low_stock = Product.objects.filter(stock__lte=10, stock__gt=0).count()
    
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    completed_orders = Order.objects.filter(status='completed').count()
    processing_orders = Order.objects.filter(status='processing').count()
    
    total_customers = Customer.objects.filter(role='customer').count()
    total_revenue = Order.objects.filter(status='completed').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Today's stats
    today = date.today()
    today_orders = Order.objects.filter(created_at__date=today).count()
    today_revenue = Order.objects.filter(created_at__date=today, status='completed').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    recent_orders = Order.objects.all().order_by('-created_at')[:5]
    recent_reservations = Reservation.objects.all().order_by('-created_at')[:5]
    low_stock_products = Product.objects.filter(stock__lte=10, stock__gt=0).order_by('stock')[:5]
    
    return render(request, 'musubiapp/admin_dashboard.html', {
        'total_products': total_products,
        'out_of_stock': out_of_stock,
        'low_stock': low_stock,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'processing_orders': processing_orders,
        'total_customers': total_customers,
        'total_revenue': total_revenue,
        'today_orders': today_orders,
        'today_revenue': today_revenue,
        'recent_orders': recent_orders,
        'recent_reservations': recent_reservations,
        'low_stock_products': low_stock_products,
    })

@admin_required
def admin_product_list(request):
    search_query = request.GET.get('search', '').strip()
    
    if search_query:
        # Search in product name, description, and category
        products = Product.objects.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__icontains=search_query)
        ).order_by('-created_at')
    else:
        products = Product.objects.all().order_by('-created_at')
    
    return render(request, 'musubiapp/admin_products.html', {
        'products': products,
        'search_query': search_query
    })

@admin_required
def admin_product_add(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description')
            price = request.POST.get('price')
            bundle_price = request.POST.get('bundle_price')
            stock = request.POST.get('stock')
            category = request.POST.get('category')
            is_active = request.POST.get('is_active') == 'on'
            
            product = Product.objects.create(
                name=name,
                description=description,
                price=price,
                bundle_price=bundle_price if bundle_price else None,
                stock=stock,
                category=category,
                is_active=is_active
            )
            
            # Handle image upload
            if 'image' in request.FILES:
                product.image = request.FILES['image']
                product.save()
            
            # Log product creation activity
            log_activity(
                user=request.user,
                action='create',
                entity_type='product',
                entity_id=product.id,
                description=f'Created product: {name} (Stock: {stock})',
                request=request
            )
            
            messages.success(request, f'Product "{name}" added successfully!')
            return redirect('admin_product_list')
            
        except Exception as e:
            messages.error(request, f'Error adding product: {str(e)}')
    
    return render(request, 'musubiapp/admin_product_form.html', {
        'form_title': 'Add New Product'
    })

@admin_required
def admin_product_edit(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        try:
            product.name = request.POST.get('name')
            product.description = request.POST.get('description')
            product.price = request.POST.get('price')
            product.bundle_price = request.POST.get('bundle_price')
            product.stock = request.POST.get('stock')
            product.category = request.POST.get('category')
            product.is_active = request.POST.get('is_active') == 'on'
            
            # Handle image upload
            if 'image' in request.FILES:
                product.image = request.FILES['image']
            
            product.save()
            
            # Log product update activity
            log_activity(
                user=request.user,
                action='update',
                entity_type='product',
                entity_id=product.id,
                description=f'Updated product: {product.name}',
                request=request
            )
            
            messages.success(request, f'Product "{product.name}" updated successfully!')
            return redirect('admin_product_list')
            
        except Exception as e:
            messages.error(request, f'Error updating product: {str(e)}')
    
    return render(request, 'musubiapp/admin_product_form.html', {
        'form_title': 'Edit Product',
        'product': product
    })

@admin_required
def admin_product_delete(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method in ['POST', 'GET']:
        product_name = product.name
        product_id = product.id
        
        # Log product deletion activity before deleting
        log_activity(
            user=request.user,
            action='delete',
            entity_type='product',
            entity_id=product_id,
            description=f'Deleted product: {product_name}',
            request=request
        )
        
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully!')
        return redirect('admin_product_list')
    
    return redirect('admin_product_list')

@admin_required
def admin_order_list(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'musubiapp/admin_orders.html', {
        'orders': orders
    })

@admin_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)
    
    # Reconstruct subtotal and delivery fee from stored total and discount
    delivery_fee = Decimal('50.00')
    subtotal = order.total_amount + order.discount_amount - delivery_fee
    
    if request.method == 'POST':
        old_status = order.status
        new_status = request.POST.get('status')
        order.status = new_status
        order.save()
        
        # Create notification for customer when status changes to preparing or shipping
        if new_status == 'preparing' and old_status != 'preparing':
            Notification.objects.create(
                user=order.customer.user,
                notification_type='order_preparing',
                title='Order is Being Prepared',
                message=f'Your order #{order.id} is now being prepared! We\'ll notify you when it\'s ready for shipping.',
                order=order
            )
        elif new_status == 'shipping' and old_status != 'shipping':
            Notification.objects.create(
                user=order.customer.user,
                notification_type='order_shipping',
                title='Order is On The Way',
                message=f'Your order #{order.id} is now out for delivery! It should arrive soon.',
                order=order
            )
        elif new_status == 'completed' and old_status != 'completed':
            Notification.objects.create(
                user=order.customer.user,
                notification_type='order_completed',
                title='Order Completed',
                message=f'Your order #{order.id} has been completed. Thank you for your purchase!',
                order=order
            )
        elif new_status == 'cancelled' and old_status != 'cancelled':
            Notification.objects.create(
                user=order.customer.user,
                notification_type='order_cancelled',
                title='Order Cancelled',
                message=f'Your order #{order.id} has been cancelled. Please contact us if you have any questions.',
                order=order
            )
        
        # Log order status change activity
        log_activity(
            user=request.user,
            action='update',
            entity_type='order',
            entity_id=order.id,
            description=f'Updated order #{order.id} status from {old_status} to {new_status}',
            request=request
        )
        
        messages.success(request, f'Order status updated to {new_status}')
        return redirect('admin_order_detail', order_id=order_id)
    
    # Check if we should highlight the status update section
    highlight_status = request.GET.get('action') == 'update_status'
    
    return render(request, 'musubiapp/admin_order_detail.html', {
        'order': order,
        'order_items': order_items,
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'highlight_status': highlight_status,
    })

@admin_required
def admin_order_add(request):
    """Admin can manually create orders"""
    if request.method == 'POST':
        try:
            customer_id = request.POST.get('customer')
            delivery_address = request.POST.get('delivery_address')
            notes = request.POST.get('notes', '')
            status = request.POST.get('status', 'pending')
            
            customer = get_object_or_404(Customer, id=customer_id)
            
            # Create order with initial total of 0
            order = Order.objects.create(
                customer=customer,
                total_amount=0,
                delivery_address=delivery_address,
                notes=notes,
                status=status
            )
            
            messages.success(request, f'Order #{order.id} created successfully! Now add items to the order.')
            return redirect('admin_order_edit', order_id=order.id)
            
        except Exception as e:
            messages.error(request, f'Error creating order: {str(e)}')
    
    customers = Customer.objects.all().select_related('user')
    return render(request, 'musubiapp/admin_order_form.html', {
        'form_title': 'Create New Order',
        'customers': customers
    })

@admin_required
def admin_order_edit(request, order_id):
    """Edit order details and manage order items"""
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_order':
            try:
                order.delivery_address = request.POST.get('delivery_address')
                order.notes = request.POST.get('notes', '')
                order.status = request.POST.get('status')
                order.save()
                messages.success(request, f'Order #{order.id} updated successfully!')
                return redirect('admin_order_edit', order_id=order_id)
            except Exception as e:
                messages.error(request, f'Error updating order: {str(e)}')
        
        elif action == 'add_item':
            try:
                product_id = request.POST.get('product')
                quantity = int(request.POST.get('quantity', 1))
                
                product = get_object_or_404(Product, id=product_id)
                
                # Check if item already exists in order
                order_item, created = OrderItem.objects.get_or_create(
                    order=order,
                    product=product,
                    defaults={'quantity': quantity, 'price': product.price}
                )
                
                if not created:
                    order_item.quantity += quantity
                    order_item.save()
                
                # Recalculate order total
                order.total_amount = sum(item.get_total() for item in order.orderitem_set.all())
                order.save()
                
                messages.success(request, f'Added {quantity}x {product.name} to order')
                return redirect('admin_order_edit', order_id=order_id)
            except Exception as e:
                messages.error(request, f'Error adding item: {str(e)}')
        
        elif action == 'remove_item':
            try:
                item_id = request.POST.get('item_id')
                order_item = get_object_or_404(OrderItem, id=item_id, order=order)
                order_item.delete()
                
                # Recalculate order total
                order.total_amount = sum(item.get_total() for item in order.orderitem_set.all())
                order.save()
                
                messages.success(request, 'Item removed from order')
                return redirect('admin_order_edit', order_id=order_id)
            except Exception as e:
                messages.error(request, f'Error removing item: {str(e)}')
    
    products = Product.objects.filter(is_active=True)
    return render(request, 'musubiapp/admin_order_edit.html', {
        'order': order,
        'order_items': order_items,
        'products': products
    })

@admin_required
def admin_inventory(request):
    products = Product.objects.all().order_by('stock')
    low_stock_products = products.filter(stock__lte=10, stock__gt=0)
    out_of_stock_products = products.filter(stock=0)
    
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        action = request.POST.get('action')
        quantity = int(request.POST.get('quantity', 0))
        notes = request.POST.get('notes', '')
        
        product = get_object_or_404(Product, id=product_id)
        previous_stock = product.stock
        
        if action == 'add':
            product.stock += quantity
            action_type = 'stock_in'
        elif action == 'remove':
            product.stock = max(0, product.stock - quantity)
            action_type = 'stock_out'
        elif action == 'update':
            product.stock = quantity
            action_type = 'adjustment'
        
        product.save()
        
        # Create inventory log
        InventoryLog.objects.create(
            product=product,
            action=action_type,
            quantity=quantity,
            previous_stock=previous_stock,
            new_stock=product.stock,
            notes=notes,
            created_by=request.user
        )
        
        messages.success(request, f'Inventory updated for {product.name}')
        return redirect('admin_inventory')
    
    return render(request, 'musubiapp/admin_inventory.html', {
        'products': products,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products
    })

@admin_required
def admin_customer_list(request):
    customers = Customer.objects.select_related('user').all().order_by('-created_at')
    return render(request, 'musubiapp/admin_customers.html', {
        'customers': customers
    })

# ============================================
# STAFF VIEWS - DISABLED (Staff functionality excluded from system)
# ============================================
# @staff_required
# def staff_dashboard(request):
#     # Staff dashboard logic
#     pending_orders = Order.objects.filter(status='pending').count()
#     preparing_orders = Order.objects.filter(status='preparing').count()
#     low_stock_count = Product.objects.filter(stock__lte=10, stock__gt=0).count()
#     out_of_stock_count = Product.objects.filter(stock=0).count()
#     
#     return render(request, 'musubiapp/staff_dashboard.html', {
#         'pending_orders': pending_orders,
#         'preparing_orders': preparing_orders,
#         'low_stock_count': low_stock_count,
#         'out_of_stock_count': out_of_stock_count,
#     })
# 
# @staff_required
# def staff_order_list(request):
#     status_filter = request.GET.get('status')
#     if status_filter:
#         orders = Order.objects.filter(status=status_filter).order_by('-created_at')
#     else:
#         orders = Order.objects.all().order_by('-created_at')
#     
#     return render(request, 'musubiapp/staff_orders.html', {
#         'orders': orders,
#         'current_status': status_filter
#     })
# 
# @staff_required
# def staff_order_detail(request, order_id):
#     order = get_object_or_404(Order, id=order_id)
#     order_items = OrderItem.objects.filter(order=order)
#     
#     if request.method == 'POST':
#         new_status = request.POST.get('status')
#         order.status = new_status
#         order.save()
#         
#         # Create notification log
#         if new_status == 'completed':
#             # Auto-reduce inventory (already handled in order completion)
#             messages.success(request, f'Order #{order.id} marked as completed! Inventory updated automatically.')
#         else:
#             messages.success(request, f'Order status updated to {new_status}')
#         
#         return redirect('staff_order_detail', order_id=order_id)
#     
#     return render(request, 'musubiapp/staff_order_detail.html', {
#         'order': order,
#         'order_items': order_items
#     })
# 
# @staff_required
# def staff_inventory(request):
#     products = Product.objects.all().order_by('stock')
#     low_stock_products = products.filter(stock__lte=10, stock__gt=0)
#     out_of_stock_products = products.filter(stock=0)
#     
#     if request.method == 'POST':
#         product_id = request.POST.get('product_id')
#         action = request.POST.get('action')
#         quantity = int(request.POST.get('quantity', 0))
#         notes = request.POST.get('notes', '')
#         
#         product = get_object_or_404(Product, id=product_id)
#         previous_stock = product.stock
#         
#         if action == 'add':
#             product.stock += quantity
#             action_type = 'stock_in'
#             message = f'Added {quantity} to {product.name} stock'
#         elif action == 'remove':
#             product.stock = max(0, product.stock - quantity)
#             action_type = 'stock_out'
#             message = f'Removed {quantity} from {product.name} stock'
#         elif action == 'update':
#             product.stock = quantity
#             action_type = 'adjustment'
#             message = f'Updated {product.name} stock to {quantity}'
#         
#         product.save()
#         
#         # Create inventory log
#         InventoryLog.objects.create(
#             product=product,
#             action=action_type,
#             quantity=quantity,
#             previous_stock=previous_stock,
#             new_stock=product.stock,
#             notes=notes,
#             created_by=request.user
#         )
#         
#         messages.success(request, message)
#         return redirect('staff_inventory')
#     
#     return render(request, 'musubiapp/staff_inventory.html', {
#         'products': products,
#         'low_stock_products': low_stock_products,
#         'out_of_stock_products': out_of_stock_products
#     })
# 
# @staff_required
# def staff_product_list(request):
#     products = Product.objects.filter(is_active=True).order_by('name')
#     return render(request, 'musubiapp/staff_products.html', {
#         'products': products
#     })
# ============================================
# END OF DISABLED STAFF VIEWS
# ============================================

# Admin Reservation CRUD Views
@admin_required
def admin_reservation_list(request):
    reservations = Reservation.objects.select_related('customer__user').prefetch_related('reservationitem_set__product').all().order_by('-reservation_date', '-reservation_time')
    return render(request, 'musubiapp/admin_reservations.html', {
        'reservations': reservations
    })

@admin_required
def admin_reservation_detail(request, reservation_id):
    """View detailed reservation information"""
    reservation = get_object_or_404(Reservation, id=reservation_id)
    reservation_items = ReservationItem.objects.filter(reservation=reservation)
    
    # Calculate totals
    total_amount = reservation.get_total_amount()
    
    if request.method == 'POST':
        # Handle status updates from detail page
        old_status = reservation.status
        new_status = request.POST.get('status')
        reservation.status = new_status
        reservation.save()
        
        # Log reservation status update
        log_activity(
            user=request.user,
            action='update',
            entity_type='reservation',
            entity_id=reservation.id,
            description=f'Admin updated reservation #{reservation.id} status from {old_status} to {new_status}',
            request=request
        )
        
        # Notify customer about status change
        if old_status != new_status:
            customer_user = reservation.customer.user
            
            if new_status == 'confirmed':
                Notification.objects.create(
                    user=customer_user,
                    notification_type='reservation_confirmed',
                    title='Reservation Confirmed',
                    message=f'Your reservation #{reservation.id} for {reservation.reservation_date} at {reservation.reservation_time} has been confirmed!',
                    reservation=reservation
                )
            elif new_status == 'cancelled':
                Notification.objects.create(
                    user=customer_user,
                    notification_type='reservation_cancelled',
                    title='Reservation Cancelled',
                    message=f'Your reservation #{reservation.id} for {reservation.reservation_date} at {reservation.reservation_time} has been cancelled.',
                    reservation=reservation
                )
            elif new_status == 'completed':
                Notification.objects.create(
                    user=customer_user,
                    notification_type='reservation_confirmed',
                    title='Reservation Completed',
                    message=f'Your reservation #{reservation.id} has been completed. Thank you for dining with us!',
                    reservation=reservation
                )
        
        messages.success(request, f'Reservation status updated to {new_status}')
        return redirect('admin_reservation_detail', reservation_id=reservation_id)
    
    # Check if we should highlight the status update section
    highlight_status = request.GET.get('action') == 'update_status'
    
    return render(request, 'musubiapp/admin_reservation_detail.html', {
        'reservation': reservation,
        'reservation_items': reservation_items,
        'total_amount': total_amount,
        'highlight_status': highlight_status,
    })

@admin_required
def admin_reservation_add(request):
    if request.method == 'POST':
        try:
            customer_id = request.POST.get('customer')
            reservation_date = request.POST.get('reservation_date')
            reservation_time = request.POST.get('reservation_time')
            number_of_guests = request.POST.get('number_of_guests')
            special_requests = request.POST.get('special_requests', '')
            status = request.POST.get('status', 'pending')
            
            customer = get_object_or_404(Customer, id=customer_id)
            
            reservation = Reservation.objects.create(
                customer=customer,
                reservation_date=reservation_date,
                reservation_time=reservation_time,
                number_of_guests=number_of_guests,
                special_requests=special_requests,
                status=status
            )
            
            # Log reservation creation activity
            log_activity(
                user=request.user,
                action='create',
                entity_type='reservation',
                entity_id=reservation.id,
                description=f'Admin created reservation #{reservation.id} for {customer.user.username} on {reservation_date}',
                request=request
            )
            
            messages.success(request, f'Reservation #{reservation.id} created successfully!')
            return redirect('admin_reservation_list')
            
        except Exception as e:
            messages.error(request, f'Error creating reservation: {str(e)}')
    
    customers = Customer.objects.filter(role='customer').select_related('user')
    products = Product.objects.filter(is_active=True)
    
    return render(request, 'musubiapp/admin_reservation_form.html', {
        'form_title': 'Add New Reservation',
        'customers': customers,
        'products': products
    })

@admin_required
def admin_reservation_edit(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    reservation_items = ReservationItem.objects.filter(reservation=reservation).select_related('product')
    
    if request.method == 'POST':
        try:
            customer_id = request.POST.get('customer')
            old_status = reservation.status
            reservation.customer = get_object_or_404(Customer, id=customer_id)
            reservation.reservation_date = request.POST.get('reservation_date')
            reservation.reservation_time = request.POST.get('reservation_time')
            reservation.number_of_guests = request.POST.get('number_of_guests')
            reservation.special_requests = request.POST.get('special_requests', '')
            new_status = request.POST.get('status')
            reservation.status = new_status
            reservation.save()
            
            # Log reservation update activity
            log_activity(
                user=request.user,
                action='update',
                entity_type='reservation',
                entity_id=reservation.id,
                description=f'Admin updated reservation #{reservation.id} - Status: {reservation.status}',
                request=request
            )
            
            # Notify customer about status change
            if old_status != new_status:
                customer_user = reservation.customer.user
                
                if new_status == 'confirmed':
                    Notification.objects.create(
                        user=customer_user,
                        notification_type='reservation_confirmed',
                        title='Reservation Confirmed',
                        message=f'Your reservation #{reservation.id} for {reservation.reservation_date} at {reservation.reservation_time} has been confirmed!',
                        reservation=reservation
                    )
                elif new_status == 'cancelled':
                    Notification.objects.create(
                        user=customer_user,
                        notification_type='reservation_cancelled',
                        title='Reservation Cancelled',
                        message=f'Your reservation #{reservation.id} for {reservation.reservation_date} at {reservation.reservation_time} has been cancelled.',
                        reservation=reservation
                    )
                elif new_status == 'completed':
                    Notification.objects.create(
                        user=customer_user,
                        notification_type='reservation_confirmed',
                        title='Reservation Completed',
                        message=f'Your reservation #{reservation.id} has been marked as completed. Thank you for dining with us!',
                        reservation=reservation
                    )
            
            messages.success(request, f'Reservation #{reservation.id} updated successfully!')
            return redirect('admin_reservation_list')
            
        except Exception as e:
            messages.error(request, f'Error updating reservation: {str(e)}')
    
    customers = Customer.objects.filter(role='customer').select_related('user')
    products = Product.objects.filter(is_active=True)
    
    return render(request, 'musubiapp/admin_reservation_form.html', {
        'form_title': 'Edit Reservation',
        'reservation': reservation,
        'reservation_items': reservation_items,
        'customers': customers,
        'products': products,
        'total_amount': reservation.get_total_amount()
    })

@admin_required
def admin_reservation_delete(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    
    if request.method == 'POST':
        reservation_info = f"#{reservation.id} - {reservation.customer.user.username}"
        reservation_id_backup = reservation.id
        reservation_date = reservation.reservation_date
        
        # Log reservation deletion activity before deleting
        log_activity(
            user=request.user,
            action='delete',
            entity_type='reservation',
            entity_id=reservation_id_backup,
            description=f'Admin deleted reservation {reservation_info} for {reservation_date}',
            request=request
        )
        
        reservation.delete()
        messages.success(request, f'Reservation {reservation_info} deleted successfully!')
        return redirect('admin_reservation_list')
    
    return render(request, 'musubiapp/admin_reservation_confirm_delete.html', {
        'reservation': reservation
    })

# Admin Customer CRUD - Enhanced
@admin_required
def admin_customer_add(request):
    if request.method == 'POST':
        try:
            # Create new user
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            
            # Check if username already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, f'Username "{username}" already exists!')
                return render(request, 'musubiapp/admin_customer_form.html', {
                    'form_title': 'Add New Customer'
                })
            
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Create customer profile
            customer = Customer.objects.create(
                user=user,
                phone=request.POST.get('phone', ''),
                address=request.POST.get('address', ''),
                role=request.POST.get('role', 'customer')
            )
            
            # Log customer creation activity
            log_activity(
                user=request.user,
                action='create',
                entity_type='customer',
                entity_id=customer.id,
                description=f'Admin created customer: {username}',
                request=request
            )
            
            messages.success(request, f'Customer "{username}" added successfully!')
            return redirect('admin_customer_list')
            
        except Exception as e:
            messages.error(request, f'Error adding customer: {str(e)}')
    
    return render(request, 'musubiapp/admin_customer_form.html', {
        'form_title': 'Add New Customer'
    })

@admin_required
def admin_customer_edit(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    user = customer.user
    
    if request.method == 'POST':
        try:
            # Update user information
            user.username = request.POST.get('username')
            user.email = request.POST.get('email')
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.save()
            
            # Update customer information
            customer.phone = request.POST.get('phone', '')
            customer.address = request.POST.get('address', '')
            customer.role = request.POST.get('role')
            customer.save()
            
            # Log customer update activity
            log_activity(
                user=request.user,
                action='update',
                entity_type='customer',
                entity_id=customer.id,
                description=f'Admin updated customer: {user.username}',
                request=request
            )
            
            messages.success(request, f'Customer "{user.username}" updated successfully!')
            return redirect('admin_customer_list')
            
        except Exception as e:
            messages.error(request, f'Error updating customer: {str(e)}')
    
    return render(request, 'musubiapp/admin_customer_form.html', {
        'form_title': 'Edit Customer',
        'customer': customer
    })

@admin_required
def admin_customer_delete(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    
    if request.method == 'POST':
        username = customer.user.username
        customer_id = customer.id
        
        # Log customer deletion activity before deleting
        log_activity(
            user=request.user,
            action='delete',
            entity_type='customer',
            entity_id=customer_id,
            description=f'Admin deleted customer: {username}',
            request=request
        )
        
        customer.user.delete()  # This will cascade delete the customer
        messages.success(request, f'Customer "{username}" deleted successfully!')
        return redirect('admin_customer_list')
    
    return render(request, 'musubiapp/admin_customer_confirm_delete.html', {
        'customer': customer
    })

@admin_required
def admin_customer_detail(request, customer_id):
    """View detailed information about a customer"""
    customer = get_object_or_404(Customer, id=customer_id)
    orders = customer.order_set.all().order_by('-created_at')
    
    # Calculate statistics
    total_orders = orders.count()
    total_spent = sum(order.total_amount for order in orders)
    pending_orders = orders.filter(status='pending').count()
    completed_orders = orders.filter(status='completed').count()
    
    return render(request, 'musubiapp/admin_customer_detail.html', {
        'customer': customer,
        'orders': orders,
        'total_orders': total_orders,
        'total_spent': total_spent,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
    })

# Admin Order CRUD - Enhanced with delete
@admin_required
def admin_order_delete(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        order_info = f"#{order.id} - {order.customer.user.username}"
        order.delete()
        messages.success(request, f'Order {order_info} deleted successfully!')
        return redirect('admin_order_list')
    
    return render(request, 'musubiapp/admin_order_confirm_delete.html', {
        'order': order
    })

# Admin InventoryLog CRUD Views
@admin_required
def admin_inventory_log_list(request):
    """View all inventory logs with filtering options"""
    logs = InventoryLog.objects.select_related('product', 'created_by').all().order_by('-created_at')
    
    # Filter by product if specified
    product_id = request.GET.get('product')
    if product_id:
        logs = logs.filter(product_id=product_id)
    
    # Filter by action type if specified
    action = request.GET.get('action')
    if action:
        logs = logs.filter(action=action)
    
    products = Product.objects.all().order_by('name')
    
    return render(request, 'musubiapp/admin_inventory_logs.html', {
        'logs': logs,
        'products': products,
        'selected_product': product_id,
        'selected_action': action
    })

@admin_required
def admin_inventory_log_detail(request, log_id):
    """View detailed information about a specific inventory log"""
    log = get_object_or_404(InventoryLog, id=log_id)
    return render(request, 'musubiapp/admin_inventory_log_detail.html', {
        'log': log
    })

@admin_required
def admin_inventory_log_delete(request, log_id):
    """Delete an inventory log (for corrections only - doesn't affect stock)"""
    log = get_object_or_404(InventoryLog, id=log_id)
    
    if request.method == 'POST':
        log_info = f"{log.action} - {log.product.name} - {log.quantity}"
        log.delete()
        messages.warning(request, f'Inventory log "{log_info}" deleted. Note: This does not restore stock levels.')
        return redirect('admin_inventory_log_list')
    
    return render(request, 'musubiapp/admin_inventory_log_confirm_delete.html', {
        'log': log
    })

# ==================== MESSAGING VIEWS ====================

# Customer Messaging Views
@customer_required
def customer_messages(request):
    """View all messages for customer"""
    received_messages = Message.objects.filter(recipient=request.user).order_by('-created_at')
    sent_messages = Message.objects.filter(sender=request.user).order_by('-created_at')
    
    # Get admin users to send messages to
    admin_users = User.objects.filter(customer__role='admin')
    
    # Count unread messages
    unread_count = received_messages.filter(is_read=False).count()
    
    return render(request, 'musubiapp/customer_messages.html', {
        'received_messages': received_messages,
        'sent_messages': sent_messages,
        'admin_users': admin_users,
        'unread_count': unread_count
    })

@customer_required
def send_message(request):
    """Send a message to admin"""
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient')
        subject = request.POST.get('subject')
        message_text = request.POST.get('message')
        
        if recipient_id and subject and message_text:
            recipient = get_object_or_404(User, id=recipient_id)
            new_message = Message.objects.create(
                sender=request.user,
                recipient=recipient,
                subject=subject,
                message=message_text
            )
            
            # Log message sending activity
            log_activity(
                user=request.user,
                action='create',
                entity_type='message',
                entity_id=new_message.id,
                description=f'Sent message to {recipient.username}: {subject}',
                request=request
            )
            
            messages.success(request, 'Message sent successfully!')
        else:
            messages.error(request, 'Please fill in all fields.')
        
        return redirect('customer_messages')
    
    return redirect('customer_messages')

@customer_required
def view_message(request, message_id):
    """View a specific message"""
    message = get_object_or_404(Message, id=message_id)
    
    # Check if user is sender or recipient
    if message.sender != request.user and message.recipient != request.user:
        messages.error(request, 'You do not have permission to view this message.')
        return redirect('customer_messages')
    
    # Mark as read if recipient is viewing
    if message.recipient == request.user and not message.is_read:
        message.is_read = True
        message.save()
        
        # Log message view activity
        log_activity(
            user=request.user,
            action='view',
            entity_type='message',
            entity_id=message.id,
            description=f'Viewed message from {message.sender.username}: {message.subject}',
            request=request
        )
    
    return render(request, 'musubiapp/view_message.html', {
        'message': message
    })

@customer_required
def delete_message(request, message_id):
    """Delete a message"""
    message = get_object_or_404(Message, id=message_id)
    
    # Only allow sender or recipient to delete
    if message.sender == request.user or message.recipient == request.user:
        message_subject = message.subject
        message_id_backup = message.id
        
        # Log message deletion activity before deleting
        log_activity(
            user=request.user,
            action='delete',
            entity_type='message',
            entity_id=message_id_backup,
            description=f'Deleted message: {message_subject}',
            request=request
        )
        
        message.delete()
        messages.success(request, 'Message deleted successfully!')
    else:
        messages.error(request, 'You do not have permission to delete this message.')
    
    return redirect('customer_messages')

# Admin Messaging Views
@admin_required
def admin_messages(request):
    """View all messages for admin"""
    received_messages = Message.objects.filter(recipient=request.user).order_by('-created_at')
    sent_messages = Message.objects.filter(sender=request.user).order_by('-created_at')
    
    # Get all customers to send messages to
    customers = User.objects.filter(customer__role='customer')
    
    # Count unread messages
    unread_count = received_messages.filter(is_read=False).count()
    
    return render(request, 'musubiapp/admin_messages.html', {
        'received_messages': received_messages,
        'sent_messages': sent_messages,
        'customers': customers,
        'unread_count': unread_count
    })

@admin_required
def admin_send_message(request):
    """Admin sends a message to customer"""
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient')
        subject = request.POST.get('subject')
        message_text = request.POST.get('message')
        
        if recipient_id and subject and message_text:
            recipient = get_object_or_404(User, id=recipient_id)
            new_message = Message.objects.create(
                sender=request.user,
                recipient=recipient,
                subject=subject,
                message=message_text
            )
            
            # Log admin message sending activity
            log_activity(
                user=request.user,
                action='create',
                entity_type='message',
                entity_id=new_message.id,
                description=f'Admin sent message to {recipient.username}: {subject}',
                request=request
            )
            
            messages.success(request, 'Message sent successfully!')
        else:
            messages.error(request, 'Please fill in all fields.')
        
        return redirect('admin_messages')
    
    return redirect('admin_messages')

@admin_required
def admin_view_message(request, message_id):
    """Admin views a specific message"""
    message = get_object_or_404(Message, id=message_id)
    
    # Check if admin is sender or recipient
    if message.sender != request.user and message.recipient != request.user:
        messages.error(request, 'You do not have permission to view this message.')
        return redirect('admin_messages')
    
    # Mark as read if recipient is viewing
    if message.recipient == request.user and not message.is_read:
        message.is_read = True
        message.save()
        
        # Log admin message view activity
        log_activity(
            user=request.user,
            action='view',
            entity_type='message',
            entity_id=message.id,
            description=f'Admin viewed message from {message.sender.username}: {message.subject}',
            request=request
        )
    
    return render(request, 'musubiapp/admin_view_message.html', {
        'message': message
    })

@admin_required
def admin_delete_message(request, message_id):
    """Admin deletes a message"""
    message = get_object_or_404(Message, id=message_id)
    
    # Only allow sender or recipient to delete
    if message.sender == request.user or message.recipient == request.user:
        message_subject = message.subject
        message_id_backup = message.id
        
        # Log admin message deletion activity before deleting
        log_activity(
            user=request.user,
            action='delete',
            entity_type='message',
            entity_id=message_id_backup,
            description=f'Admin deleted message: {message_subject}',
            request=request
        )
        
        message.delete()
        messages.success(request, 'Message deleted successfully!')
    else:
        messages.error(request, 'You do not have permission to delete this message.')
    
    return redirect('admin_messages')

# Customer Order History View
@customer_required
def customer_order_history(request):
    """View customer's order history"""
    customer = request.user.customer
    orders = Order.objects.filter(customer=customer).order_by('-created_at')
    
    return render(request, 'musubiapp/order_history.html', {
        'orders': orders
    })

@customer_required
def customer_order_detail(request, order_id):
    """View detailed information about a specific order"""
    customer = request.user.customer
    order = get_object_or_404(Order, id=order_id, customer=customer)
    order_items = OrderItem.objects.filter(order=order)
    
    return render(request, 'musubiapp/customer_order_detail.html', {
        'order': order,
        'order_items': order_items
    })

# Product Search and Filter
def product_search(request):
    """Search and filter products"""
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    sort_by = request.GET.get('sort', 'name')
    
    products = Product.objects.filter(is_active=True)
    
    # Search by name or description
    if query:
        products = products.filter(name__icontains=query) | products.filter(description__icontains=query)
    
    # Filter by category
    if category:
        products = products.filter(category=category)
    
    # Filter by price range
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Sorting
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('name')
    
    # Get all categories for filter
    categories = Product.objects.values_list('category', flat=True).distinct()
    
    return render(request, 'musubiapp/product_list.html', {
        'products': products,
        'categories': categories,
        'query': query,
        'selected_category': category,
        'sort_by': sort_by
    })

# Sales Analytics
@admin_required
def admin_sales_analytics(request):
    """View sales analytics and reports"""
    # Date range filter
    days = int(request.GET.get('days', 30))
    start_date = date.today() - timedelta(days=days)
    
    # Total sales
    total_sales = Order.objects.filter(
        status='completed',
        created_at__gte=start_date
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Orders by status
    orders_by_status = Order.objects.filter(
        created_at__gte=start_date
    ).values('status').annotate(count=Count('id'))
    
    # Top selling products
    top_products = OrderItem.objects.filter(
        order__status='completed',
        order__created_at__gte=start_date
    ).values('product__name').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('price')
    ).order_by('-total_quantity')[:10]
    
    # Daily sales
    daily_sales = Order.objects.filter(
        status='completed',
        created_at__gte=start_date
    ).extra(
        select={'day': 'DATE(created_at)'}
    ).values('day').annotate(
        total=Sum('total_amount'),
        count=Count('id')
    ).order_by('day')
    
    # Customer statistics
    top_customers = Order.objects.filter(
        status='completed',
        created_at__gte=start_date
    ).values('customer__user__username').annotate(
        total_spent=Sum('total_amount'),
        order_count=Count('id')
    ).order_by('-total_spent')[:10]
    
    return render(request, 'musubiapp/admin_sales_analytics.html', {
        'total_sales': total_sales,
        'orders_by_status': orders_by_status,
        'top_products': top_products,
        'daily_sales': daily_sales,
        'top_customers': top_customers,
        'days': days
    })

# Notification Views
@login_required
def customer_notifications(request):
    """View customer notifications"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()
    
    return render(request, 'musubiapp/notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count
    })

@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('customer_notifications')

@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('customer_notifications')

@login_required
def delete_notification(request, notification_id):
    """Delete a notification"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    
    if request.method == 'POST':
        notification.delete()
        messages.success(request, 'Notification deleted successfully!')
    
    return redirect('customer_notifications')

@login_required
def get_unread_notifications_count(request):
    """Get unread notifications count (AJAX)"""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})

@admin_required
def admin_notifications(request):
    """View admin notifications with order management"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()
    
    return render(request, 'musubiapp/admin_notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count
    })

@admin_required
def accept_order(request, order_id):
    """Accept a pending order and change status to preparing"""
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        if order.status == 'pending':
            # Update order status to preparing
            order.status = 'preparing'
            order.save()
            
            # Create notification for customer
            Notification.objects.create(
                user=order.customer.user,
                notification_type='order_preparing',
                title='Order is Being Prepared',
                message=f'Your order #{order.id} has been accepted and is now being prepared!',
                order=order
            )
            
            # Mark the admin's notification as read
            Notification.objects.filter(
                user=request.user,
                order=order,
                notification_type='new_order',
                is_read=False
            ).update(is_read=True)
            
            messages.success(request, f'Order #{order.id} has been accepted and is now being prepared!')
        else:
            messages.warning(request, f'Order #{order.id} is already {order.get_status_display()}.')
    
    return redirect('admin_notifications')

# Activity Log Views
@admin_required
def admin_activity_log(request):
    """View activity logs with filtering"""
    logs = ActivityLog.objects.select_related('user').all()
    
    # Get filter parameters
    action_filter = request.GET.get('action', '')
    entity_filter = request.GET.get('entity', '')
    user_filter = request.GET.get('user', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Apply filters
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    if entity_filter:
        logs = logs.filter(entity_type=entity_filter)
    
    if user_filter:
        logs = logs.filter(user__username__icontains=user_filter)
    
    if date_from:
        logs = logs.filter(created_at__date__gte=date_from)
    
    if date_to:
        logs = logs.filter(created_at__date__lte=date_to)
    
    # Get unique users for filter dropdown
    users = User.objects.filter(activity_logs__isnull=False).distinct()
    
    # Pagination (show 50 per page)
    from django.core.paginator import Paginator
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'musubiapp/admin_activity_log.html', {
        'page_obj': page_obj,
        'logs': page_obj.object_list,
        'users': users,
        'action_filter': action_filter,
        'entity_filter': entity_filter,
        'user_filter': user_filter,
        'date_from': date_from,
        'date_to': date_to,
        'action_choices': ActivityLog.ACTION_TYPES,
        'entity_choices': ActivityLog.ENTITY_TYPES,
    })

# Analytics Report Views
@admin_required
def admin_analytics(request):
    """View analytics report with filtering"""
    from datetime import datetime, timedelta
    from django.db.models import Sum, Count, Avg, F
    from django.db.models.functions import TruncDate, TruncMonth
    
    # Get filter parameters
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    report_type = request.GET.get('report_type', 'overview')
    
    # Default date range (last 30 days)
    if not date_from:
        date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = datetime.now().strftime('%Y-%m-%d')
    
    # Convert to datetime objects
    start_date = datetime.strptime(date_from, '%Y-%m-%d')
    end_date = datetime.strptime(date_to, '%Y-%m-%d')
    
    # Base querysets with date filter
    orders = Order.objects.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)
    
    # Overview Statistics
    total_orders = orders.count()
    total_revenue = orders.aggregate(total=Sum('total_amount'))['total'] or 0
    avg_order_value = orders.aggregate(avg=Avg('total_amount'))['avg'] or 0
    
    # Order Status Breakdown
    status_breakdown = orders.values('status').annotate(count=Count('id')).order_by('status')
    
    # Revenue by Date
    revenue_by_date = orders.annotate(date=TruncDate('created_at')).values('date').annotate(
        revenue=Sum('total_amount'),
        orders=Count('id')
    ).order_by('date')
    
    # Top Products
    top_products = OrderItem.objects.filter(
        order__created_at__date__gte=start_date,
        order__created_at__date__lte=end_date
    ).values('product__name').annotate(
        quantity_sold=Sum('quantity'),
        revenue=Sum(F('quantity') * F('price'))
    ).order_by('-quantity_sold')[:10]
    
    # Top Customers
    top_customers = orders.values(
        'customer__user__username',
        'customer__user__first_name',
        'customer__user__last_name'
    ).annotate(
        total_orders=Count('id'),
        total_spent=Sum('total_amount')
    ).order_by('-total_spent')[:10]
    
    # Product Category Performance
    category_performance = OrderItem.objects.filter(
        order__created_at__date__gte=start_date,
        order__created_at__date__lte=end_date
    ).values('product__category').annotate(
        quantity_sold=Sum('quantity'),
        revenue=Sum(F('quantity') * F('price'))
    ).order_by('-revenue')
    
    # New Customers
    new_customers = Customer.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).count()
    
    # Inventory Status
    total_products = Product.objects.count()
    out_of_stock = Product.objects.filter(stock=0).count()
    low_stock = Product.objects.filter(stock__lte=10, stock__gt=0).count()
    
    # Daily Orders Chart Data
    daily_orders = orders.annotate(date=TruncDate('created_at')).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Monthly Revenue (if date range > 60 days)
    date_diff = (end_date - start_date).days
    if date_diff > 60:
        monthly_revenue = orders.annotate(month=TruncMonth('created_at')).values('month').annotate(
            revenue=Sum('total_amount'),
            orders=Count('id')
        ).order_by('month')
    else:
        monthly_revenue = None
    
    # Calculate growth rates
    previous_start = start_date - timedelta(days=(end_date - start_date).days)
    previous_orders = Order.objects.filter(
        created_at__date__gte=previous_start,
        created_at__date__lt=start_date
    )
    previous_revenue = previous_orders.aggregate(total=Sum('total_amount'))['total'] or 0
    previous_order_count = previous_orders.count()
    
    if previous_revenue > 0:
        revenue_growth = ((total_revenue - previous_revenue) / previous_revenue) * 100
    else:
        revenue_growth = 100 if total_revenue > 0 else 0
    
    if previous_order_count > 0:
        order_growth = ((total_orders - previous_order_count) / previous_order_count) * 100
    else:
        order_growth = 100 if total_orders > 0 else 0
    
    context = {
        'date_from': date_from,
        'date_to': date_to,
        'report_type': report_type,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'avg_order_value': avg_order_value,
        'status_breakdown': status_breakdown,
        'revenue_by_date': revenue_by_date,
        'top_products': top_products,
        'top_customers': top_customers,
        'category_performance': category_performance,
        'new_customers': new_customers,
        'total_products': total_products,
        'out_of_stock': out_of_stock,
        'low_stock': low_stock,
        'daily_orders': daily_orders,
        'monthly_revenue': monthly_revenue,
        'revenue_growth': revenue_growth,
        'order_growth': order_growth,
    }
    
    return render(request, 'musubiapp/admin_analytics.html', context)

# Review and Feedback Views
@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    customer = request.user.customer
    
    # Check if customer has purchased this product
    has_purchased = OrderItem.objects.filter(
        order__customer=customer,
        product=product,
        order__status='completed'
    ).exists()
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        title = request.POST.get('title')
        comment = request.POST.get('comment')
        image = request.FILES.get('image')
        
        if not all([rating, title, comment]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('product_detail', product_id=product_id)
        
        # Check if user already reviewed this product
        existing_review = Review.objects.filter(
            product=product,
            customer=customer
        ).first()
        
        if existing_review:
            messages.warning(request, 'You have already reviewed this product.')
            return redirect('product_detail', product_id=product_id)
        
        review = Review.objects.create(
            product=product,
            customer=customer,
            rating=int(rating),
            title=title,
            comment=comment,
            image=image,
            is_verified_purchase=has_purchased
        )
        
        # Log activity
        log_activity(
            user=request.user,
            action='create',
            entity_type='product',
            entity_id=product.id,
            description=f'Added review for {product.name}',
            request=request
        )
        
        messages.success(request, 'Thank you for your review!')
        return redirect('product_detail', product_id=product_id)
    
    return redirect('product_detail', product_id=product_id)

@login_required
def submit_feedback(request):
    if request.method == 'POST':
        customer = request.user.customer
        feedback_type = request.POST.get('feedback_type', 'general')
        subject = request.POST.get('subject')
        message_text = request.POST.get('message')
        
        if not all([subject, message_text]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('customer_feedback')
        
        feedback = Feedback.objects.create(
            customer=customer,
            feedback_type=feedback_type,
            subject=subject,
            message=message_text,
            status='new'
        )
        
        # Log activity
        log_activity(
            user=request.user,
            action='create',
            entity_type='system',
            description=f'Submitted feedback: {subject}',
            request=request
        )
        
        messages.success(request, 'Thank you for your feedback! We will review it shortly.')
        return redirect('customer_feedback')
    
    return render(request, 'musubiapp/customer_feedback.html')

@login_required
def customer_feedback(request):
    customer = request.user.customer
    feedbacks = Feedback.objects.filter(customer=customer).order_by('-created_at')
    
    return render(request, 'musubiapp/customer_feedback.html', {
        'feedbacks': feedbacks
    })

@admin_required
def admin_feedback_list(request):
    status_filter = request.GET.get('status', 'all')
    type_filter = request.GET.get('type', 'all')
    
    feedbacks = Feedback.objects.all()
    
    if status_filter != 'all':
        feedbacks = feedbacks.filter(status=status_filter)
    
    if type_filter != 'all':
        feedbacks = feedbacks.filter(feedback_type=type_filter)
    
    feedbacks = feedbacks.order_by('-created_at')
    
    return render(request, 'musubiapp/admin_feedback_list.html', {
        'feedbacks': feedbacks,
        'status_filter': status_filter,
        'type_filter': type_filter
    })

@admin_required
def admin_feedback_detail(request, feedback_id):
    feedback = get_object_or_404(Feedback, id=feedback_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'respond':
            response = request.POST.get('response')
            feedback.admin_response = response
            feedback.responded_by = request.user
            feedback.responded_at = timezone.now()
            feedback.status = 'resolved'
            feedback.save()
            
            messages.success(request, 'Response sent successfully!')
            
        elif action == 'update_status':
            new_status = request.POST.get('status')
            feedback.status = new_status
            feedback.save()
            
            messages.success(request, f'Status updated to {feedback.get_status_display()}')
        
        return redirect('admin_feedback_detail', feedback_id=feedback_id)
    
    return render(request, 'musubiapp/admin_feedback_detail.html', {
        'feedback': feedback
    })

@admin_required
def admin_reviews_list(request):
    reviews = Review.objects.select_related('product', 'customer__user').order_by('-created_at')
    
    return render(request, 'musubiapp/admin_reviews_list.html', {
        'reviews': reviews
    })

@admin_required
def admin_review_toggle_approval(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    review.is_approved = not review.is_approved
    review.save()
    
    status = 'approved' if review.is_approved else 'hidden'
    messages.success(request, f'Review {status} successfully!')
    
    return redirect('admin_reviews_list')

@admin_required
def admin_review_delete(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    product_name = review.product.name
    review.delete()
    
    messages.success(request, f'Review for {product_name} deleted successfully!')
    return redirect('admin_reviews_list')