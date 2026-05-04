import traceback
import google.generativeai as genai

from django.conf import settings
from django.http import StreamingHttpResponse

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from course.models import Course, Lecture

from .models import ChatMessage, ChatSession
from .serializers import ChatMessageSerializer, ChatSessionSerializer
from .vector_store import get_vector_store


def _format_context_for_prompt(context_results: list[dict]) -> tuple[str, list[dict]]:
    """
    Build a formatted context string for the AI system prompt, and return
    a list of video citation metadata for constructing timestamp links.

    Returns:
        (context_text, citations)
        - context_text: multiline string injected into system prompt
        - citations: list of {lecture_id, title, display_time, video_url} for transcript chunks
    """
    if not context_results:
        return "No specific course context found.", []

    text_blocks = []
    transcript_blocks = []
    citations = []

    for r in context_results:
        if r.get("content_type") == "transcript" and r.get("display_time"):
            # Transcript chunk with timestamp
            tag = f"[VIDEO:{r['lecture_id']}@{r['display_time']}]"
            transcript_blocks.append(
                f"{tag} [{r['title']} — {r['display_time']}]\n{r['document']}"
            )
            citations.append({
                "lecture_id": r["lecture_id"],
                "title": r["title"],
                "display_time": r["display_time"],
                "timestamp_start": r.get("timestamp_start", 0),
                "video_url": r.get("video_url", ""),
            })
        else:
            # Plain text content
            text_blocks.append(
                f"[TEXT] [{r['title']}]\n{r['document']}"
            )

    parts = []
    if text_blocks:
        parts.append("### Course Materials\n" + "\n\n".join(text_blocks))
    if transcript_blocks:
        parts.append(
            "### Video Transcript Segments (with timestamps)\n"
            "When you reference these, always include the timestamp citation.\n\n"
            + "\n\n".join(transcript_blocks)
        )

    return "\n\n".join(parts), citations


def _build_system_prompt(course, context_text: str, citations: list[dict]) -> str:
    """Build the full system prompt with context and timestamp citation instructions."""

    has_video_context = bool(citations)

    citation_instruction = ""
    if has_video_context:
        citation_instruction = """
CRITICAL — VIDEO TIMESTAMP CITATIONS:
When your answer is based on a video transcript segment marked with [VIDEO:ID@MM:SS], you MUST include a clickable timestamp reference in your reply using this EXACT format:

[▶ Xem tại MM:SS](#video-ts?lecture=ID&t=SECONDS)

Rules:
- Replace MM:SS with the actual display time (e.g., 02:34)
- Replace ID with the lecture ID number
- Replace SECONDS with the integer start time in seconds
- Place the link naturally after the relevant sentence
- You may include 1-3 citations per answer if multiple segments are relevant
- If you cite from a transcript, always include the timestamp link — do not omit it

Example: "Khái niệm này được giải thích rõ ràng tại phần mở đầu. [▶ Xem tại 01:30](#video-ts?lecture=42&t=90)"
"""

    return f"""You are an expert AI Teaching Assistant for the course "{course.title}".
Course Category: {course.category.name if course.category else 'N/A'}

Your role is to help students understand the course material based strictly on the provided context.
If a question is not covered by the context, kindly say so and suggest they ask the instructor.

Format all responses using Markdown. Be concise, clear, and friendly.
{citation_instruction}
--- COURSE CONTEXT ---
{context_text}
----------------------"""


class ChatWidgetAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_or_create_session(self, user, course_id):
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return None, None, Response(
                {"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND
            )

        session, _ = ChatSession.objects.get_or_create(user=user, course=course)
        return session, course, None

    def get(self, request):
        course_id = request.query_params.get('course_id')
        if not course_id:
            return Response(
                {"error": "course_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        session, course, error_response = self._get_or_create_session(request.user, course_id)
        if error_response:
            return error_response

        serializer = ChatSessionSerializer(session)
        return Response(serializer.data)

    def post(self, request):
        course_id = request.data.get('course_id')
        user_message_content = request.data.get('message')

        if not course_id or not user_message_content:
            return Response(
                {"error": "course_id and message are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session, course, error_response = self._get_or_create_session(request.user, course_id)
        if error_response:
            return error_response

        # Save user message
        user_message = ChatMessage.objects.create(
            session=session, role='user', content=user_message_content
        )

        # --- RAG: Retrieve relevant context with timestamp metadata ---
        vs = get_vector_store()
        context_results = vs.query_course_context(
            course.id, user_message_content, n_results=5
        )
        context_text, citations = _format_context_for_prompt(context_results)

        # Build system prompt with timestamp citation instructions
        system_prompt = _build_system_prompt(course, context_text, citations)

        # Get conversation history
        history_msgs = session.messages.all().order_by('created_at')
        gemini_history = [
            {"role": msg.role, "parts": [msg.content]}
            for msg in history_msgs
            if msg.role in ['user', 'model'] and msg.id != user_message.id
        ]

        def generate():
            try:
                api_key = getattr(settings, 'GEMINI_API_KEY', None)
                if not api_key:
                    msg = "AI assistant is not configured (missing API key)."
                    ChatMessage.objects.create(session=session, role='model', content=msg)
                    yield msg
                    return

                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(
                    settings.AI_MODEL, system_instruction=system_prompt
                )

                chat = model.start_chat(history=gemini_history)
                response = chat.send_message(user_message_content, stream=True)

                full_reply = ""
                for chunk in response:
                    yield chunk.text
                    full_reply += chunk.text

                # Save assistant message after stream finishes
                ChatMessage.objects.create(
                    session=session, role='model', content=full_reply
                )
            except Exception as e:
                traceback.print_exc()
                yield f"\n\nError communicating with AI: {str(e)}"

        return StreamingHttpResponse(generate(), content_type='text/plain')


class LectureVideoInfoAPIView(APIView):
    """
    Returns video URL and metadata for a specific lecture.
    Used by the frontend to construct timestamp deep links.
    GET /api/chat/lecture-video/<lecture_id>/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, lecture_id):
        try:
            lecture = Lecture.objects.select_related(
                'section__course'
            ).get(id=lecture_id)
        except Lecture.DoesNotExist:
            return Response(
                {"error": "Lecture not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Ensure user is enrolled or is instructor
        course = lecture.section.course
        user = request.user
        is_enrolled = course.enrollments.filter(student=user).exists()
        is_instructor = (course.instructor == user)

        if not (is_enrolled or is_instructor or user.is_superuser):
            return Response(
                {"error": "Not authorized"}, status=status.HTTP_403_FORBIDDEN
            )

        video_url = lecture.video_url or (lecture.video_file.url if lecture.video_file else "")

        return Response({
            "lecture_id": lecture.id,
            "title": lecture.title,
            "video_url": video_url,
            "course_slug": course.slug,
            "video_source": lecture.video_source,
            "duration": lecture.duration,
        })


class CourseInsightsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        course_id = request.query_params.get('course_id')
        if not course_id:
            return Response(
                {"error": "course_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response(
                {"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if course.instructor != request.user and not request.user.is_superuser:
            return Response(
                {"error": "Not authorized"}, status=status.HTTP_403_FORBIDDEN
            )

        recent_questions = ChatMessage.objects.filter(
            session__course=course, role='user'
        ).order_by('-created_at')[:100]

        if not recent_questions.exists():
            return Response({"report": "Not enough student questions yet to generate insights."})

        questions_text = "\n".join([f"- {msg.content}" for msg in recent_questions])

        system_prompt = f"""You are a curriculum analyst for the course '{course.title}'.
Analyze the raw student questions provided below.
Return a summary in Markdown format identifying:
1. The top 3 concepts students are struggling with.
2. Suggestions for what the instructor should add or improve in the curriculum.
Keep it actionable and concise."""

        try:
            api_key = getattr(settings, 'GEMINI_API_KEY', None)
            if not api_key:
                return Response({"report": "API Key is missing, unable to generate insights."})

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(settings.AI_MODEL, system_instruction=system_prompt)
            response = model.generate_content(questions_text)
            report = response.text
        except Exception as e:
            traceback.print_exc()
            return Response(
                {"error": "Failed to generate AI insights."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({"report": report})


def _build_sales_system_prompt() -> str:
    courses = Course.objects.filter(status='published').select_related('category')
    course_list = []
    for c in courses:
        cat_name = c.category.name if c.category else 'General'
        price = "Free" if c.is_free else f"${c.current_price}"
        course_list.append(f"- **{c.title}** ({cat_name}) | Price: {price} | URL Slug: `{c.slug}`\n  Description: {c.subtitle}")
    
    catalog_text = "\n".join(course_list) if course_list else "No courses currently available."

    return f"""You are 'Studigo Sales Assistant', a helpful and friendly AI for the Studigo online course marketplace.
Your goal is to help users discover the best courses for their needs, answer questions about pricing, and guide them to enroll.

Here is the current catalog of available courses:
{catalog_text}

Rules:
1. Only recommend courses from the catalog provided above.
2. If a user asks for a topic not in the catalog, politely inform them we don't have it yet.
3. Keep responses concise, engaging, and structured with markdown.
4. When recommending a course, always provide the exact course URL formatted as: [Course Title](/course/URL_Slug)
"""

class SalesChatAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_or_create_session(self, user):
        # course=None represents the general sales session
        session, _ = ChatSession.objects.get_or_create(user=user, course=None)
        return session

    def get(self, request):
        session = self._get_or_create_session(request.user)
        serializer = ChatSessionSerializer(session)
        return Response(serializer.data)

    def post(self, request):
        user_message_content = request.data.get('message')

        if not user_message_content:
            return Response(
                {"error": "message is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session = self._get_or_create_session(request.user)

        # Save user message
        user_message = ChatMessage.objects.create(
            session=session, role='user', content=user_message_content
        )

        system_prompt = _build_sales_system_prompt()

        # Get conversation history
        history_msgs = session.messages.all().order_by('created_at')
        gemini_history = [
            {"role": msg.role, "parts": [msg.content]}
            for msg in history_msgs
            if msg.role in ['user', 'model'] and msg.id != user_message.id
        ]

        def generate():
            try:
                api_key = getattr(settings, 'GEMINI_API_KEY', None)
                if not api_key:
                    msg = "Sales assistant is not configured (missing API key)."
                    ChatMessage.objects.create(session=session, role='model', content=msg)
                    yield msg
                    return

                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(
                    settings.AI_MODEL, system_instruction=system_prompt
                )

                chat = model.start_chat(history=gemini_history)
                response = chat.send_message(user_message_content, stream=True)

                full_reply = ""
                for chunk in response:
                    yield chunk.text
                    full_reply += chunk.text

                # Save assistant message after stream finishes
                ChatMessage.objects.create(
                    session=session, role='model', content=full_reply
                )
            except Exception as e:
                traceback.print_exc()
                yield f"\n\nError communicating with AI: {str(e)}"

        return StreamingHttpResponse(generate(), content_type='text/plain')
