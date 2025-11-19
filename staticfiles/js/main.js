// static/js/main.js
class MusubiApp {
    constructor() {
        this.init();
    }

    init() {
        this.initNavigation();
        this.initCartFunctionality();
        this.initForms();
        this.initUIComponents();
    }

    initNavigation() {
        // Mobile menu toggle (if needed)
        const mobileMenuBtn = document.getElementById('mobileMenuBtn');
        const navLinks = document.querySelector('.nav-links');
        
        if (mobileMenuBtn && navLinks) {
            mobileMenuBtn.addEventListener('click', () => {
                navLinks.classList.toggle('active');
            });
        }

        // Active link highlighting
        this.highlightActiveLink();
    }

    highlightActiveLink() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.nav-links a');
        
        navLinks.forEach(link => {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
    }

    initCartFunctionality() {
        // Global add to cart buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('add-to-cart') || 
                e.target.closest('.add-to-cart')) {
                const button = e.target.classList.contains('add-to-cart') ? 
                    e.target : e.target.closest('.add-to-cart');
                this.handleAddToCart(button);
            }
        });
    }

    async handleAddToCart(button) {
        const productId = button.getAttribute('data-product-id');
        
        if (!productId) {
            console.error('No product ID found');
            return;
        }

        // Show loading state
        const originalText = button.innerHTML;
        button.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Adding...';
        button.disabled = true;

        try {
            const response = await fetch(`/add-to-cart/${productId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                },
            });

            const data = await response.json();
            
            if (data.success) {
                this.showToast('Product added to cart!', 'success');
                this.updateCartCount(data.cart_count);
            } else {
                this.showToast(data.error || 'Error adding product to cart', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error adding product to cart', 'error');
        } finally {
            // Restore button state
            button.innerHTML = originalText;
            button.disabled = false;
        }
    }

    initForms() {
        // Form validation and enhancement
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        });
    }

    async handleFormSubmit(event) {
        const form = event.target;
        
        // Add loading state to submit button
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Processing...';
            submitBtn.disabled = true;

            // Revert after processing (you might want to do this in the response handler)
            setTimeout(() => {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }, 3000);
        }
    }

    initUIComponents() {
        // Initialize tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });

        // Initialize popovers
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }

    updateCartCount(count) {
        const cartBadges = document.querySelectorAll('.cart-count');
        cartBadges.forEach(badge => {
            badge.textContent = count;
        });
    }

    showToast(message, type = 'info') {
        // Create toast container if it doesn't exist
        let toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toastContainer';
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }

        // Create toast
        const toastId = 'toast-' + Date.now();
        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'info'} border-0`;
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        toastContainer.appendChild(toast);

        // Show toast
        const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
        bsToast.show();

        // Remove toast after hide
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
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

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.musubiApp = new MusubiApp();
});

// Utility functions
function formatPrice(amount) {
    return '₱' + parseFloat(amount).toFixed(2);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}