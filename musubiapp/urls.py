"""URL configuration for musubiapp."""

from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.customer_login, name='customer_login'),
    path('register/', views.register, name='register'),
    path('logout/', views.custom_logout, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', views.reset_password, name='reset_password'),
    path('menu/', views.product_list, name='product_list'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/update-address/', views.update_address, name='update_address'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('cart/update/<int:cart_item_id>/', views.update_cart, name='update_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    
    # Admin dashboard
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    # Staff dashboard - DISABLED
    # path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    
    # Custom Admin CRUD URLs - Products
    path('admin/products/', views.admin_product_list, name='admin_product_list'),
    path('admin/products/add/', views.admin_product_add, name='admin_product_add'),
    path('admin/products/edit/<int:product_id>/', views.admin_product_edit, name='admin_product_edit'),
    path('admin/products/delete/<int:product_id>/', views.admin_product_delete, name='admin_product_delete'),
    
    # Admin Orders CRUD
    path('admin/orders/', views.admin_order_list, name='admin_order_list'),
    path('admin/orders/add/', views.admin_order_add, name='admin_order_add'),
    path('admin/orders/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('admin/orders/edit/<int:order_id>/', views.admin_order_edit, name='admin_order_edit'),
    path('admin/orders/delete/<int:order_id>/', views.admin_order_delete, name='admin_order_delete'),
    
    # Admin Customers CRUD
    path('admin/customers/', views.admin_customer_list, name='admin_customer_list'),
    path('admin/customers/add/', views.admin_customer_add, name='admin_customer_add'),
    path('admin/customers/<int:customer_id>/', views.admin_customer_detail, name='admin_customer_detail'),
    path('admin/customers/edit/<int:customer_id>/', views.admin_customer_edit, name='admin_customer_edit'),
    path('admin/customers/delete/<int:customer_id>/', views.admin_customer_delete, name='admin_customer_delete'),
    
    # Admin Reservations CRUD
    path('admin/reservations/', views.admin_reservation_list, name='admin_reservation_list'),
    path('admin/reservations/add/', views.admin_reservation_add, name='admin_reservation_add'),
    path('admin/reservations/<int:reservation_id>/', views.admin_reservation_detail, name='admin_reservation_detail'),
    path('admin/reservations/edit/<int:reservation_id>/', views.admin_reservation_edit, name='admin_reservation_edit'),
    path('admin/reservations/delete/<int:reservation_id>/', views.admin_reservation_delete, name='admin_reservation_delete'),
    
    # Admin Inventory Management (backend remains available, even if menu links are hidden)
    path('admin/inventory/', views.admin_inventory, name='admin_inventory'),
    
    # Admin Inventory Logs CRUD
    path('admin/inventory-logs/', views.admin_inventory_log_list, name='admin_inventory_log_list'),
    path('admin/inventory-logs/<int:log_id>/', views.admin_inventory_log_detail, name='admin_inventory_log_detail'),
    path('admin/inventory-logs/delete/<int:log_id>/', views.admin_inventory_log_delete, name='admin_inventory_log_delete'),
    
    # Customer Messaging
    path('messages/', views.customer_messages, name='customer_messages'),
    path('messages/send/', views.send_message, name='send_message'),
    path('messages/view/<int:message_id>/', views.view_message, name='view_message'),
    path('messages/delete/<int:message_id>/', views.delete_message, name='delete_message'),
    
    # Admin Messaging
    path('admin/messages/', views.admin_messages, name='admin_messages'),
    path('admin/messages/send/', views.admin_send_message, name='admin_send_message'),
    path('admin/messages/view/<int:message_id>/', views.admin_view_message, name='admin_view_message'),
    path('admin/messages/delete/<int:message_id>/', views.admin_delete_message, name='admin_delete_message'),
    
    # Customer Order History
    path('orders/', views.customer_order_history, name='customer_order_history'),
    path('orders/<int:order_id>/', views.customer_order_detail, name='customer_order_detail'),
    
    # Customer Reservations
    path('reservations/', views.customer_reservations, name='customer_reservations'),
    path('reservations/create/', views.customer_reservation_create, name='customer_reservation_create'),
    path('reservations/<int:reservation_id>/', views.customer_reservation_detail, name='customer_reservation_detail'),
    path('reservations/<int:reservation_id>/cancel/', views.customer_reservation_cancel, name='customer_reservation_cancel'),
    
    # Product Search
    path('products/', views.product_list, name='products'),
    path('search/', views.product_search, name='product_search'),
    
    # Admin Analytics (single analytics entry point)
    path('admin/analytics/', views.admin_analytics, name='admin_analytics'),
    
    # Notifications
    path('notifications/', views.customer_notifications, name='customer_notifications'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/delete/<int:notification_id>/', views.delete_notification, name='delete_notification'),
    path('api/notifications/unread-count/', views.get_unread_notifications_count, name='get_unread_notifications_count'),
    
    # Admin Notifications
    path('admin/notifications/', views.admin_notifications, name='admin_notifications'),
    path('admin/orders/accept/<int:order_id>/', views.accept_order, name='accept_order'),
    
    # Activity Log
    path('admin/activity-log/', views.admin_activity_log, name='admin_activity_log'),
    
    # Reviews and Ratings
    path('product/<int:product_id>/review/', views.add_review, name='add_review'),
    path('admin/reviews/', views.admin_reviews_list, name='admin_reviews_list'),
    path('admin/reviews/<int:review_id>/toggle/', views.admin_review_toggle_approval, name='admin_review_toggle_approval'),
    
    # Debug view
    path('debug/media/', views.debug_media, name='debug_media'),
    path('test/images/', views.test_images, name='test_images'),
    path('admin/reviews/<int:review_id>/delete/', views.admin_review_delete, name='admin_review_delete'),
    
    # Customer Feedback
    path('feedback/', views.customer_feedback, name='customer_feedback'),
    path('feedback/submit/', views.submit_feedback, name='submit_feedback'),
    path('admin/feedback/', views.admin_feedback_list, name='admin_feedback_list'),
    path('admin/feedback/<int:feedback_id>/', views.admin_feedback_detail, name='admin_feedback_detail'),

    # Staff URLs - DISABLED (Staff functionality excluded from system)
    # path('staff/orders/', views.staff_order_list, name='staff_orders'),
    # path('staff/orders/<int:order_id>/', views.staff_order_detail, name='staff_order_detail'),
    # path('staff/inventory/', views.staff_inventory, name='staff_inventory'),
    # path('staff/products/', views.staff_product_list, name='staff_products'),
]

if settings.DEBUG:
    # Serve media files (uploaded images) during development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)