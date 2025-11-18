# Create new file: musubiapp/backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from .models import Customer

class RoleBasedAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                # Check if user has a customer profile and is approved
                try:
                    customer = user.customer
                    if customer.is_approved:
                        return user
                except Customer.DoesNotExist:
                    # Allow users without customer profile (superusers)
                    return user
        except User.DoesNotExist:
            return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None