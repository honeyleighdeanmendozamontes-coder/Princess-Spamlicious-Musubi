// static/js/cart.js
class CartManager {
    constructor() {
        this.initEventListeners();
    }

    initEventListeners() {
        // Quantity updates
        document.querySelectorAll('.quantity-input').forEach(input => {
            input.addEventListener('change', (e) => this.updateQuantity(e));
        });

        // Remove items
        document.querySelectorAll('.remove-item').forEach(button => {
            button.addEventListener('click', (e) => this.removeItem(e));
        });

        // Clear cart
        const clearCartBtn = document.getElementById('clearCart');
        if (clearCartBtn) {
            clearCartBtn.addEventListener('click', (e) => this.clearCart(e));
        }
    }

    async updateQuantity(event) {
        const input = event.target;
        const cartItemId = input.getAttribute('data-cart-item-id');
        const quantity = parseInt(input.value);
        const maxStock = parseInt(input.getAttribute('max'));

        if (quantity < 1 || quantity > maxStock) {
            this.showAlert('Invalid quantity', 'error');
            input.value = input.getAttribute('data-old-value');
            return;
        }

        try {
            const response = await fetch(`/update-cart/${cartItemId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    quantity: quantity,
                    action: 'update'
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.updateCartTotals(data);
                this.showAlert('Cart updated successfully', 'success');
            } else {
                this.showAlert(data.error || 'Error updating cart', 'error');
                input.value = input.getAttribute('data-old-value');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Error updating cart', 'error');
            input.value = input.getAttribute('data-old-value');
        }
    }

    async removeItem(event) {
        const button = event.target.closest('.remove-item');
        const cartItemId = button.getAttribute('data-cart-item-id');

        if (!confirm('Remove this item from cart?')) {
            return;
        }

        try {
            const response = await fetch(`/update-cart/${cartItemId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: 'remove'
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.removeCartItem(cartItemId);
                this.updateCartTotals(data);
                this.showAlert('Item removed from cart', 'success');
            } else {
                this.showAlert(data.error || 'Error removing item', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Error removing item', 'error');
        }
    }

    async clearCart(event) {
        event.preventDefault();

        if (!confirm('Clear all items from cart?')) {
            return;
        }

        try {
            const response = await fetch('/clear-cart/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                }
            });

            const data = await response.json();
            
            if (data.success) {
                location.reload(); // Reload to show empty cart
            } else {
                this.showAlert(data.error || 'Error clearing cart', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Error clearing cart', 'error');
        }
    }

    removeCartItem(cartItemId) {
        const itemElement = document.querySelector(`[data-cart-item-id="${cartItemId}"]`).closest('.cart-item');
        if (itemElement) {
            itemElement.remove();
        }
    }

    updateCartTotals(data) {
        // Update subtotal
        const subtotalElement = document.querySelector('.subtotal');
        if (subtotalElement) {
            subtotalElement.textContent = `₱${data.total}`;
        }

        // Update total
        const totalElement = document.querySelector('.total-amount');
        if (totalElement) {
            const deliveryFee = 50; // Assuming fixed delivery fee
            totalElement.textContent = `₱${data.total + deliveryFee}`;
        }

        // Update cart count in navbar
        this.updateCartCount(data.cart_count);
    }

    updateCartCount(count) {
        const cartBadge = document.querySelector('.cart-count');
        if (cartBadge) {
            cartBadge.textContent = count;
        }
    }

    showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Add to messages container or create one
        let messagesContainer = document.querySelector('.messages');
        if (!messagesContainer) {
            messagesContainer = document.createElement('div');
            messagesContainer.className = 'messages container mt-3';
            document.querySelector('nav').after(messagesContainer);
        }
        
        messagesContainer.appendChild(alertDiv);
        
        setTimeout(() => {
            alertDiv.remove();
        }, 3000);
    }

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

// Initialize cart manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new CartManager();
});