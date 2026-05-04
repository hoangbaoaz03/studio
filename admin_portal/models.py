from django.db import models
from django.conf import settings


class AdminPermission(models.Model):
    """
    Stores which admin portal modules a staff user is allowed to access.
    Superusers bypass this entirely — they always see everything.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='admin_permissions'
    )
    allowed_modules = models.JSONField(
        default=list,
        help_text="List of module keys this admin can access, e.g. ['dashboard','courses','categories']"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} — {', '.join(self.allowed_modules)}"
