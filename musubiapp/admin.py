# musubiapp/admin.py
from django.contrib import admin
from .models import Customer, Product, Order, OrderItem, Cart, CartItem, InventoryLog, Reservation, ReservationItem

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['price', 'stock', 'is_active']

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['customer', 'total_items', 'total_price', 'created_at']
    search_fields = ['customer__user__username']

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity', 'get_total']
    list_filter = ['product__category']
    
    def get_total(self, obj):
        return obj.get_total()
    get_total.short_description = 'Total'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['customer__user__username', 'id']
    list_editable = ['status']

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price', 'get_total']
    list_filter = ['product__category']
    
    def get_total(self, obj):
        return obj.get_total()
    get_total.short_description = 'Total'

@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ['product', 'action', 'quantity', 'previous_stock', 'new_stock', 'created_by', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['product__name']
    readonly_fields = ['created_at']

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'reservation_date', 'reservation_time', 'number_of_guests', 'status', 'get_total_amount', 'created_at']
    list_filter = ['status', 'reservation_date', 'created_at']
    search_fields = ['customer__user__username', 'id']
    list_editable = ['status']
    date_hierarchy = 'reservation_date'
    
    def get_total_amount(self, obj):
        return f"₱{obj.get_total_amount():.2f}"
    get_total_amount.short_description = 'Pre-order Total'

@admin.register(ReservationItem)
class ReservationItemAdmin(admin.ModelAdmin):
    list_display = ['reservation', 'product', 'quantity', 'price', 'get_total']
    list_filter = ['product__category', 'reservation__status']
    search_fields = ['reservation__id', 'product__name']
    
    def get_total(self, obj):
        return f"₱{obj.get_total():.2f}"
    get_total.short_description = 'Total'