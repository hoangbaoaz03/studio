"""
Django signals for the chat app.
Listens for Lecture video changes and auto-triggers transcript indexing.
"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


def _has_video_file(lecture) -> bool:
    """Return True if the lecture has an accessible video file."""
    if lecture.lecture_type != "video":
        return False
    return bool(lecture.video_file or lecture.video_url)


@receiver(post_save, sender="course.Lecture")
def on_lecture_saved(sender, instance, created, **kwargs):
    """
    Auto-index transcript when a video lecture is saved with a video file.
    
    Trigger conditions:
    - Lecture type is 'video'
    - lecture.video_file is set (direct upload) OR video_url starts with /media/
    
    Uses '__original_video_file' tracking to only trigger when the video ACTUALLY changed,
    not on every incidental save (e.g., updating title, description, etc.)
    """
    if instance.lecture_type != "video":
        return

    # Check if video file actually changed (we track the original value in __init__)
    original_video_file = getattr(instance, "_original_video_file", None)
    original_video_url = getattr(instance, "_original_video_url", None)

    current_video_file = instance.video_file.name if instance.video_file else None
    current_video_url = instance.video_url or None

    video_file_changed = current_video_file != original_video_file
    video_url_changed = (
        current_video_url != original_video_url
        and current_video_url
        and current_video_url.startswith("/media/")
    )

    has_video = bool(current_video_file or (current_video_url and current_video_url.startswith("/media/")))

    if not has_video:
        return

    should_index = created or video_file_changed or video_url_changed

    if not should_index:
        return

    logger.info(
        f"[Signal] Lecture '{instance.title}' (ID={instance.id}) video changed → "
        "queuing transcript indexing."
    )

    # Import here to avoid circular imports at module level
    from chat.tasks import index_lecture_transcript_async
    index_lecture_transcript_async(lecture_id=instance.id, force=True)
