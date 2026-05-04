"""
Management command to extract transcripts from video lectures and index them
into the vector store with timestamps for use by the AI chatbot.

Usage:
    python manage.py index_video_transcripts --course_id=5
    python manage.py index_video_transcripts --all
    python manage.py index_video_transcripts --lecture_id=42
    python manage.py index_video_transcripts --course_id=5 --force
"""
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from chat.transcript_service import (
    chunk_transcript_segments,
    extract_transcript_from_video,
)
from chat.vector_store import get_vector_store
from course.models import Course, Lecture


class Command(BaseCommand):
    help = "Extract and index video transcripts with timestamps for AI chatbot RAG."

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--course_id", type=int,
            help="Index transcripts for all video lectures in this course."
        )
        group.add_argument(
            "--lecture_id", type=int,
            help="Index transcript for a single lecture."
        )
        group.add_argument(
            "--all", action="store_true", dest="all_courses",
            help="Index transcripts for ALL published courses (slow!)."
        )
        parser.add_argument(
            "--force", action="store_true",
            help="Re-index even if transcript already exists."
        )

    def handle(self, *args, **options):
        vs = get_vector_store()

        # Collect lectures to process
        if options.get("lecture_id"):
            try:
                lectures = [Lecture.objects.select_related(
                    "section__course"
                ).get(id=options["lecture_id"])]
            except Lecture.DoesNotExist:
                self.stderr.write(self.style.ERROR(
                    f"Lecture {options['lecture_id']} not found."
                ))
                return
        elif options.get("course_id"):
            course_id = options["course_id"]
            try:
                course = Course.objects.get(id=course_id)
            except Course.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"Course {course_id} not found."))
                return
            lectures = list(
                Lecture.objects.filter(
                    section__course=course,
                    lecture_type="video",
                ).select_related("section__course")
            )
            self.stdout.write(f"Course: {course.title} — {len(lectures)} video lecture(s) found.")
        else:
            # --all
            lectures = list(
                Lecture.objects.filter(
                    lecture_type="video",
                    section__course__status="published",
                ).select_related("section__course")
            )
            self.stdout.write(f"All courses — {len(lectures)} video lecture(s) found.")

        if not lectures:
            self.stdout.write(self.style.WARNING("No video lectures to index."))
            return

        ok_count = 0
        skip_count = 0
        fail_count = 0

        for lecture in lectures:
            course = lecture.section.course
            self.stdout.write(
                f"\n[{course.title}] → Lecture: {lecture.title} (ID: {lecture.id})"
            )

            # Resolve video file path
            video_path = self._resolve_video_path(lecture)
            if not video_path:
                self.stdout.write(self.style.WARNING(
                    "  ⚠ No local video file found. Skipping."
                ))
                skip_count += 1
                continue

            if not os.path.exists(video_path):
                self.stdout.write(self.style.WARNING(
                    f"  ⚠ File not accessible: {video_path}. Skipping."
                ))
                skip_count += 1
                continue

            # Check if already indexed (unless --force)
            if not options.get("force"):
                import sqlite3
                was_indexed = self._is_already_indexed(vs, course.id, lecture.id)
                if was_indexed:
                    self.stdout.write(
                        f"  ✓ Already indexed (use --force to re-index)."
                    )
                    skip_count += 1
                    continue

            self.stdout.write(f"  → Extracting transcript from: {video_path}")
            self.stdout.write("    (Uploading to Gemini... this may take a few minutes)")

            segments = extract_transcript_from_video(video_path)

            if not segments:
                self.stdout.write(self.style.ERROR(
                    "  ✗ Transcript extraction failed or returned empty."
                ))
                fail_count += 1
                continue

            self.stdout.write(f"  ✓ Got {len(segments)} raw segments. Chunking...")

            chunks = chunk_transcript_segments(segments, max_words=150)
            self.stdout.write(f"  → {len(chunks)} chunks to embed.")

            # Clear old transcript data before re-indexing
            vs.delete_lecture_transcript(course.id, lecture.id)

            # Build video URL for deep links
            video_url = self._get_video_url(lecture)

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

            self.stdout.write(self.style.SUCCESS(
                f"  ✅ Indexed {indexed}/{len(chunks)} chunks for '{lecture.title}'."
            ))
            ok_count += 1

        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS(
            f"Done! ✅ Indexed: {ok_count}  ⚠ Skipped: {skip_count}  ✗ Failed: {fail_count}"
        ))

    def _resolve_video_path(self, lecture: Lecture) -> str | None:
        """
        Get absolute local path to video file.
        Handles both FileField (video_file) and MEDIA_ROOT-relative paths.
        """
        # Priority 1: Direct FileField
        if lecture.video_file and lecture.video_file.name:
            abs_path = os.path.join(settings.MEDIA_ROOT, lecture.video_file.name)
            if os.path.exists(abs_path):
                return abs_path
            # FileField may already contain full path
            if os.path.exists(lecture.video_file.name):
                return lecture.video_file.name

        # Priority 2: video_url pointing to local media
        if lecture.video_url and lecture.video_url.startswith("/media/"):
            rel = lecture.video_url.lstrip("/media/")
            abs_path = os.path.join(settings.MEDIA_ROOT, rel)
            if os.path.exists(abs_path):
                return abs_path

        return None

    def _get_video_url(self, lecture: Lecture) -> str:
        """Return the best available video URL for the lecture."""
        if lecture.video_url:
            return lecture.video_url
        if lecture.video_file:
            return lecture.video_file.url
        return ""

    def _is_already_indexed(self, vs, course_id: int, lecture_id: int) -> bool:
        """Return True if any transcript chunk exists for this lecture."""
        try:
            cursor = vs.conn.cursor()
            cursor.execute(
                "SELECT 1 FROM embeddings WHERE course_id=? AND lecture_id=? AND content_type='transcript' LIMIT 1",
                (course_id, lecture_id)
            )
            return cursor.fetchone() is not None
        except Exception:
            return False
