from django.core.management.base import BaseCommand # type: ignore
from course.models import Course, Lecture
from chat.vector_store import get_vector_store
from chat.utils import extract_text_from_resource

class Command(BaseCommand):
    help = 'Syncs course textual content to ChromaDB for RAG context.'

    def add_arguments(self, parser):
        parser.add_argument('--course_id', type=int, help='Specific course ID to sync. If omitted, syncs all active courses.')

    def handle(self, *args, **options):
        course_id = options.get('course_id')
        vs = get_vector_store()

        if course_id:
            courses = Course.objects.filter(id=course_id)
        else:
            courses = Course.objects.filter(status='published')

        if not courses.exists():
            self.stdout.write(self.style.WARNING("No courses found to sync."))
            return

        for course in courses:
            self.stdout.write(f"Syncing course: {course.title} (ID: {course.id})")
            
            # Sync syllabus info
            desc = course.description or ""
            desc_vi = course.description_vi or ""
            learn = ', '.join(course.what_you_will_learn) if course.what_you_will_learn else ""
            learn_vi = ', '.join(course.what_you_will_learn_vi) if course.what_you_will_learn_vi else ""
            req = ', '.join(course.requirements) if course.requirements else ""
            req_vi = ', '.join(course.requirements_vi) if course.requirements_vi else ""
            
            content = f"Course Description:\n{desc}\n{desc_vi}\n\nWhat you will learn:\n{learn}\n{learn_vi}\n\nRequirements:\n{req}\n{req_vi}"
            
            vs.add_lecture_content(
                course.id, 
                0, 
                "Course Syllabus Structure (Goals, Description, Requirements)", 
                content
            )

            for section in course.sections.all().prefetch_related('lectures', 'lectures__course_resources'):
                for lecture in section.lectures.all():
                    content_str = ""
                    if lecture.content:
                        content_str += f"Summary: {lecture.content}\n"
                    if lecture.article_content:
                        content_str += f"Content: {lecture.article_content}\n"
                        
                    for resource in lecture.course_resources.all():
                        resource_text = extract_text_from_resource(resource)
                        if resource_text.strip():
                            content_str += f"\n[Attached PDF: {resource.title}]\n{resource_text}"
                            
                    if content_str.strip():
                        vs.add_lecture_content(course.id, lecture.id, lecture.title, content_str)
                        self.stdout.write(f"  - Indexed lecture: {lecture.title}")

        self.stdout.write(self.style.SUCCESS("✅ Vector sync complete!"))
