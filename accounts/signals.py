from .models import InstructorProfile

def post_save_account_receiver(instance=None, created=False, *args, **kwargs):
    """
    Handle post-creation logic for User
    """
    if created:
        # Create InstructorProfile if user is an instructor
        if instance.is_instructor:
            InstructorProfile.objects.get_or_create(user=instance)
