// static/js/inventory.js
class InventoryManager {
    constructor() {
        this.initEventListeners();
        this.initSearchAndFilter();
    }

    initEventListeners() {
        // Stock update forms
        document.querySelectorAll('.stock-update-form').forEach(form => {
            form.addEventListener('submit', (e) => this.handleStockUpdate(e));
        });

        // Low stock alerts
        this.checkLowStock();
    }

    initSearchAndFilter() {
        const searchInput = document.getElementById('inventorySearch');
        const statusFilter = document.getElementById('statusFilter');

        if (searchInput) {
            searchInput.addEventListener('input', () => this.filterProducts());
        }

        if (statusFilter) {
            statusFilter.addEventListener('change', () => this.filterProducts());
        }
    }

    async handleStockUpdate(event) {
        event.preventDefault();
        
        const form = event.target;
        const productId = form.getAttribute('data-product-id');
        const stockInput = form.querySelector('input[name="stock"]');
        const newStock = parseInt(stockInput.value);

        if (isNaN(newStock) || newStock < 0) {
            this.showAlert('Please enter a valid stock quantity', 'error');
            return;
        }

        try {
            const response = await fetch(`/update-stock/${productId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    stock: newStock
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.updateProductRow(data.product);
                this.showAlert('Stock updated successfully', 'success');
                this.updateInventoryStats();
            } else {
                this.showAlert(data.error || 'Error updating stock', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert('Error updating stock', 'error');
        }
    }

    updateProductRow(product) {
        const row = document.querySelector(`[data-product-id="${product.id}"]`);
        if (row) {
            // Update stock cell
            const stockCell = row.querySelector('.stock-quantity');
            if (stockCell) {
                stockCell.textContent = product.stock;
            }

            // Update status badge
            const statusCell = row.querySelector('.stock-status');
            if (statusCell) {
                let statusText, statusClass;
                if (product.stock === 0) {
                    statusText = 'Out of Stock';
                    statusClass = 'bg-danger';
                } else if (product.stock <= 10) {
                    statusText = 'Low Stock';
                    statusClass = 'bg-warning';
                } else {
                    statusText = 'In Stock';
                    statusClass = 'bg-success';
                }
                
                statusCell.innerHTML = `<span class="badge ${statusClass}">${statusText}</span>`;
            }
        }
    }

    filterProducts() {
        const searchTerm = document.getElementById('inventorySearch').value.toLowerCase();
        const statusFilter = document.getElementById('statusFilter').value;
        const productRows = document.querySelectorAll('[data-product-id]');

        productRows.forEach(row => {
            const productName = row.querySelector('.product-name').textContent.toLowerCase();
            const statusBadge = row.querySelector('.stock-status .badge').textContent.toLowerCase();
            
            const matchesSearch = productName.includes(searchTerm);
            const matchesStatus = !statusFilter || 
                (statusFilter === 'out' && statusBadge.includes('out of stock')) ||
                (statusFilter === 'low' && statusBadge.includes('low stock')) ||
                (statusFilter === 'in' && statusBadge.includes('in stock'));
            
            if (matchesSearch && matchesStatus) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    checkLowStock() {
        const lowStockItems = document.querySelectorAll('.bg-warning');
        if (lowStockItems.length > 0) {
            console.log(`⚠️ ${lowStockItems.length} items are low in stock`);
            // You could add a notification system here
        }
    }

    updateInventoryStats() {
        // This would typically refresh the stats from the server
        // For now, we'll just log the action
        console.log('Inventory stats updated');
    }

    showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container-fluid');
        container.insertBefore(alertDiv, container.firstChild);
        
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

// Initialize inventory manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new InventoryManager();
});