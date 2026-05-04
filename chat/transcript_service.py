"""
Transcript service for extracting timestamped content from video lectures.
Uses Gemini File API to process uploaded video files and return transcript segments
with start/end times. Supports Vietnamese and English automatically.
"""
import os
import re
import time
import json
import logging

import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)


def _parse_timestamp_to_seconds(ts: str) -> float:
    """Convert MM:SS or HH:MM:SS string to total seconds."""
    parts = ts.strip().split(":")
    try:
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    except (ValueError, IndexError):
        pass
    return 0.0


def _seconds_to_mmss(seconds: float) -> str:
    """Convert seconds to MM:SS display string."""
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    return f"{m:02d}:{s:02d}"


def _parse_gemini_transcript(raw_text: str) -> list[dict]:
    """
    Parse Gemini's timestamped transcript output.
    Expected format from Gemini:
        [00:00] Text here...
        [01:23] More text...
    Returns list of {start_seconds, end_seconds, text}
    """
    # Match lines like [MM:SS] or [HH:MM:SS] followed by text
    pattern = re.compile(
        r'\[(\d{1,2}:\d{2}(?::\d{2})?)\]\s*(.+?)(?=\n\[|\Z)',
        re.DOTALL
    )

    matches = pattern.findall(raw_text)
    segments = []

    for i, (ts_str, text) in enumerate(matches):
        start = _parse_timestamp_to_seconds(ts_str)
        # end = start of next segment, or start + 60 for the last one
        if i + 1 < len(matches):
            end = _parse_timestamp_to_seconds(matches[i + 1][0])
        else:
            end = start + 60.0
        
        cleaned_text = text.strip().replace('\n', ' ')
        if cleaned_text:
            segments.append({
                "start_seconds": start,
                "end_seconds": end,
                "text": cleaned_text,
                "display_time": _seconds_to_mmss(start),
            })

    return segments


def extract_transcript_from_video(video_file_path: str) -> list[dict]:
    """
    Upload a local video file to Gemini File API and extract a timestamped transcript.
    
    Args:
        video_file_path: Absolute path to the local video file.
        
    Returns:
        List of transcript segments:
        [
            {
                "start_seconds": 0.0,
                "end_seconds": 45.2,
                "text": "Xin chào các bạn, hôm nay chúng ta sẽ học...",
                "display_time": "00:00"
            },
            ...
        ]
        Returns empty list if extraction fails or file not found.
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not api_key:
        logger.error("GEMINI_API_KEY is not set. Cannot extract transcript.")
        return []

    if not os.path.exists(video_file_path):
        logger.error(f"Video file not found: {video_file_path}")
        return []

    genai.configure(api_key=api_key)

    logger.info(f"Uploading video to Gemini File API: {video_file_path}")
    
    try:
        # Step 1: Upload file
        video_file = genai.upload_file(
            path=video_file_path,
            display_name=os.path.basename(video_file_path),
        )

        # Step 2: Wait for processing
        max_wait = 300  # 5 minutes
        waited = 0
        while video_file.state.name == "PROCESSING" and waited < max_wait:
            logger.info(f"Waiting for Gemini to process video... ({waited}s)")
            time.sleep(10)
            waited += 10
            video_file = genai.get_file(video_file.name)

        if video_file.state.name != "ACTIVE":
            logger.error(f"Gemini file processing failed. State: {video_file.state.name}")
            _safe_delete_gemini_file(video_file)
            return []

        # Step 3: Request timestamped transcript
        ai_model_name = getattr(settings, 'AI_MODEL', 'gemini-2.5-flash')
        model = genai.GenerativeModel(ai_model_name)
        prompt = """Analyze this educational video and generate a detailed transcript with timestamps.

IMPORTANT RULES:
1. Start every segment with a timestamp in the format [MM:SS]
2. Add a new timestamp every 30-60 seconds, or at every topic change
3. Detect and transcribe in the original language (Vietnamese or English) — do NOT translate
4. Be accurate and complete
5. Each timestamped segment should be on its own line

Example format:
[00:00] Xin chào các bạn, trong bài học hôm nay chúng ta sẽ tìm hiểu về...
[00:45] Phần đầu tiên là khái niệm cơ bản về...
[01:30] Hello everyone, in today's lesson we will explore...

Now transcribe the video:"""

        response = model.generate_content([video_file, prompt])
        raw_transcript = response.text

        logger.info(f"Gemini transcript received. Length: {len(raw_transcript)} chars")

        # Step 4: Parse and return segments
        segments = _parse_gemini_transcript(raw_transcript)
        logger.info(f"Parsed {len(segments)} transcript segments.")

        # Step 5: Cleanup Gemini file (to avoid storage quota usage)
        _safe_delete_gemini_file(video_file)

        return segments

    except Exception as e:
        logger.error(f"Error extracting transcript: {e}", exc_info=True)
        return []


def _safe_delete_gemini_file(gemini_file):
    """Delete uploaded file from Gemini to free quota."""
    try:
        genai.delete_file(gemini_file.name)
        logger.info(f"Deleted Gemini file: {gemini_file.name}")
    except Exception as e:
        logger.warning(f"Could not delete Gemini file {gemini_file.name}: {e}")


def chunk_transcript_segments(
    segments: list[dict],
    max_words: int = 150,
    overlap_segments: int = 1,
) -> list[dict]:
    """
    Group transcript segments into larger chunks for embedding.
    Each chunk will be a window of consecutive segments.
    
    Args:
        segments: List of segments from extract_transcript_from_video()
        max_words: Approximate max words per chunk
        overlap_segments: Number of segments to overlap between chunks
        
    Returns:
        List of chunks with combined text and timestamp range info.
    """
    if not segments:
        return []

    chunks = []
    i = 0
    
    while i < len(segments):
        chunk_segs = []
        word_count = 0
        j = i
        
        while j < len(segments) and word_count < max_words:
            seg = segments[j]
            chunk_segs.append(seg)
            word_count += len(seg["text"].split())
            j += 1

        if chunk_segs:
            combined_text = " ".join(s["text"] for s in chunk_segs)
            chunks.append({
                "text": combined_text,
                "start_seconds": chunk_segs[0]["start_seconds"],
                "end_seconds": chunk_segs[-1]["end_seconds"],
                "display_time": chunk_segs[0]["display_time"],
            })

        # Advance with overlap
        i = max(i + 1, j - overlap_segments)

    return chunks
