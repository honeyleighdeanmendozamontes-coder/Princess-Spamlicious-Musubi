import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "musubiproject.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

USERNAME = "adminleigh"
EMAIL = "adminleigh@example.com"
PASSWORD = "Admin6789"

if not User.objects.filter(username=USERNAME).exists():
    User.objects.create_superuser(
        username=USERNAME,
        email=EMAIL,
        password=PASSWORD
    )

       