"""
Background tasks for chat/RAG processing.
Uses Python threading (no Celery/Redis required).
Runs transcript indexing asynchronously so video upload API returns instantly.
"""
import logging
import threading

logger = logging.getLogger(__name__)


def _run_index_lecture_transcript(lecture_id: int, force: bool = False):
    """
    Internal function that runs in a background thread.
    Extracts transcript from a lecture's video file and stores it in the vector store.
    """
    import django
    # Ensure Django apps are ready (needed when running in threads)
    try:
        from django.apps import apps
        if not apps.ready:
            django.setup()
    except Exception:
        pass

    try:
        from django.conf import settings
        from course.models import Lecture
        from chat.transcript_service import (
            chunk_transcript_segments,
            extract_transcript_from_video,
        )
        from chat.vector_store import get_vector_store
        import os

        logger.info(f"[TranscriptTask] Starting for lecture_id={lecture_id}")

        try:
            lecture = Lecture.objects.select_related("section__course").get(id=lecture_id)
        except Lecture.DoesNotExist:
            logger.error(f"[TranscriptTask] Lecture {lecture_id} not found.")
            return

        course = lecture.section.course

        # Check already indexed (skip unless force=True)
        vs = get_vector_store()
        if not force:
            cursor = vs.conn.cursor()
            cursor.execute(
                "SELECT 1 FROM embeddings WHERE course_id=? AND lecture_id=? AND content_type='transcript' LIMIT 1",
                (course.id, lecture_id)
            )
            if cursor.fetchone():
                logger.info(
                    f"[TranscriptTask] Lecture {lecture_id} already indexed. Skipping."
                )
                return

        # Resolve video file path
        video_path = None

        if lecture.video_file and lecture.video_file.name:
            abs_path = os.path.join(settings.MEDIA_ROOT, lecture.video_file.name)
            if os.path.exists(abs_path):
                video_path = abs_path
            elif os.path.exists(str(lecture.video_file.name)):
                video_path = str(lecture.video_file.name)

        if not video_path and lecture.video_url and lecture.video_url.startswith("/media/"):
            rel = lecture.video_url.lstrip("/media/")
            abs_path = os.path.join(settings.MEDIA_ROOT, rel)
            if os.path.exists(abs_path):
                video_path = abs_path

        if not video_path:
            logger.warning(
                f"[TranscriptTask] No accessible local video file for lecture {lecture_id}. "
                "Transcript indexing skipped."
            )
            return

        logger.info(f"[TranscriptTask] Extracting transcript from: {video_path}")
        segments = extract_transcript_from_video(video_path)

        if not segments:
            logger.error(
                f"[TranscriptTask] Transcript extraction failed for lecture {lecture_id}."
            )
            return

        chunks = chunk_transcript_segments(segments, max_words=150)
        logger.info(
            f"[TranscriptTask] Got {len(segments)} segments → {len(chunks)} chunks. Embedding..."
        )

        # Clear old data before re-indexing
        vs.delete_lecture_transcript(course.id, lecture_id)

        video_url = lecture.video_url or (
            lecture.video_file.url if lecture.video_file else ""
        )

        indexed = 0
        for chunk in chunks:
            success = vs.add_transcript_chunk(
                course_id=course.id,
                lecture_id=lecture.id,
                title=lecture.title,
                text=chunk["text"],
                start_seconds=chunk["start_seconds"],
                end_seconds=chunk["end_seconds"],
                display_time=chunk["display_time"],
                video_url=video_url,
            )
            if success:
                indexed += 1

        logger.info(
            f"[TranscriptTask] ✅ Done! Indexed {indexed}/{len(chunks)} chunks "
            f"for lecture '{lecture.title}' (course: {course.title})"
        )

    except Exception as exc:
        logger.error(
            f"[TranscriptTask] Unexpected error for lecture_id={lecture_id}: {exc}",
            exc_info=True,
        )


def index_lecture_transcript_async(lecture_id: int, force: bool = False):
    """
    Queue transcript indexing for a lecture to run in a background thread.
    Returns immediately — the API response is not blocked.
    
    Args:
        lecture_id: ID of the Lecture to index.
        force: If True, re-index even if transcript already exists.
    """
    thread = threading.Thread(
        target=_run_index_lecture_transcript,
        args=(lecture_id, force),
        daemon=True,   # Thread dies when main process exits
        name=f"transcript-index-{lecture_id}",
    )
    thread.start()
    logger.info(
        f"[TranscriptTask] Background thread started for lecture_id={lecture_id}"
    )
