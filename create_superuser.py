import os
import sys

# Set Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "musubiproject.settings")

try:
    import django
    django.setup()

    from django.contrib.auth import get_user_model

    User = get_user_model()
    username = "admin"
    email = "admin@example.com"
    password = "password123"

    if User.objects.filter(username=username).exists():
        print("Superuser already exists.")
    else:
        # Ensure flags are set even if a custom user model overrides defaults
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )
        # In case the custom user model does not set these flags automatically
        changed = False
        if hasattr(user, "is_staff") and not getattr(user, "is_staff"):
            user.is_staff = True
            changed = True
        if hasattr(user, "is_superuser") and not getattr(user, "is_superuser"):
            user.is_superuser = True
            changed = True
        if changed:
            user.save(update_fields=["is_staff", "is_superuser"])  # type: ignore[arg-type]
        print("Superuser created successfully.")
except Exception as e:
    # Keep output minimal as requested; but exit non-zero so Render shows failure if needed
    # You can inspect logs on Render if this fails
    sys.exit(1)
