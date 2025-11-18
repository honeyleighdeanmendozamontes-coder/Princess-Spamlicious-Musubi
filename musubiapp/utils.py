# musubiapp/utils.py
from .models import ActivityLog

def log_activity(user, action, entity_type, entity_id=None, description='', request=None):
    """
    Helper function to log user activities
    
    Args:
        user: User object
        action: Action type (create, update, delete, login, logout, view)
        entity_type: Type of entity (product, order, customer, etc.)
        entity_id: ID of the entity (optional)
        description: Description of the activity
        request: HTTP request object (optional, for IP and user agent)
    """
    ip_address = None
    user_agent = None
    
    if request:
        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        # Get user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    ActivityLog.objects.create(
        user=user,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent
    )
