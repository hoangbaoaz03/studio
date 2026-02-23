
import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from course.models import Category, Course

# Category Mapping
CATEGORY_MAP = {
    "Development": "Lập trình",
    "Business": "Kinh doanh",
    "Finance & Accounting": "Tài chính & Kế toán",
    "IT & Software": "CNTT & Phần mềm",
    "Office Productivity": "Năng suất văn phòng",
    "Personal Development": "Phát triển cá nhân",
    "Design": "Thiết kế",
    "Marketing": "Marketing",
    "Web Development": "Lập trình Web",
    "Data Science": "Khoa học Dữ liệu",
    "Mobile Development": "Lập trình Di động",
    "Python": "Python",
    "JavaScript": "JavaScript",
    "React": "React",
    "Excel": "Excel",
}

def translate_categories():
    print("Translating Categories...")
    for cat in Category.objects.all():
        if cat.name in CATEGORY_MAP:
            cat.name_vi = CATEGORY_MAP[cat.name]
            print(f"Updated Category: {cat.name} -> {cat.name_vi}")
            cat.save()
        else:
            # Simple fallback or keep English if untranslatable
            print(f"Skipping Category (No map): {cat.name}")

# Course Keyword Mapping
COURSE_KEYWORD_MAP = {
    "Complete": "Toàn diện",
    "Bootcamp": "Trại huấn luyện",
    "Web Development": "Lập trình Web",
    "Machine Learning": "Học máy",
    "Data Science": "Khoa học Dữ liệu",
    "Financial Analysis": "Phân tích Tài chính",
    "Introduction": "Giới thiệu",
    "Basics": "Cơ bản",
    "Masterclass": "Lớp học chuyên sâu",
    "Beginner": "Người mới bắt đầu",
    "Advanced": "Nâng cao",
    "Guide": "Hướng dẫn",
    "Angular": "Angular",
    "React": "React",
    "Python": "Python",
    "Java": "Java",
    "AWS": "AWS",
    "Certification": "Chứng chỉ",
    "Excel": "Excel",
}

def translate_courses():
    print("\nTranslating Courses...")
    for course in Course.objects.all():
        # Title translation (naive replacement)
        new_title = course.title
        for eng, vi in COURSE_KEYWORD_MAP.items():
            new_title = new_title.replace(eng, vi)
        
        # Fallback if no specific keywords matched significantly
        if new_title == course.title:
            new_title = f"{course.title} (Bản tiếng Việt)"
            
        course.title_vi = new_title
        
        # Subtitle translation
        if course.subtitle:
            course.subtitle_vi = f"{course.subtitle} (Đã dịch)"
        else:
            course.subtitle_vi = "Một khóa học tuyệt vời để bắt đầu sự nghiệp của bạn."

        # Description translation (dummy)
        if not course.description_vi:
            course.description_vi = f"""
            **Mô tả khóa học**
            
            Đây là phiên bản tiếng Việt của khóa học "{course.title}".
            
            Trong khóa học này, bạn sẽ học:
            - Các kiến thức cơ bản và nâng cao về chủ đề này.
            - Cách áp dụng vào thực tế thông qua các dự án.
            - Mẹo và thủ thuật từ chuyên gia.
            
            Khóa học này phù hợp cho cả người mới bắt đầu và những người đã có kinh nghiệm muốn nâng cao kỹ năng.
            """

        # List fields translation
        def translate_list(items):
            translated = []
            for item in items:
                new_item = item
                # Simple keyword replacement
                replacements = {
                    "Learn": "Học",
                    "Understand": "Hiểu",
                    "Build": "Xây dựng",
                    "Create": "Tạo",
                    "Master": "Làm chủ",
                    "Basic": "Cơ bản",
                    "Advanced": "Nâng cao",
                    "No requirements": "Không có yêu cầu",
                    "Computer": "Máy tính",
                    "access": "truy cập",
                    "Mac": "Mac",
                    "PC": "PC",
                    "Any": "Bất kỳ",
                    "developers": "lập trình viên",
                    "Students": "Sinh viên",
                    "Beginners": "Người mới bắt đầu",
                    "Everything": "Mọi thứ",
                    "From scratch": "Từ con số 0"
                }
                for eng, vi in replacements.items():
                    new_item = new_item.replace(eng, vi).replace(eng.lower(), vi.lower())
                
                # If simplified translation didn't change much, append marker only if not already there
                if new_item == item and "(Tiếng Việt)" not in new_item:
                     new_item = f"{item} (Tiếng Việt)"
                
                translated.append(new_item)
            return translated

        if course.what_you_will_learn:
            course.what_you_will_learn_vi = translate_list(course.what_you_will_learn)
        
        if course.requirements:
            course.requirements_vi = translate_list(course.requirements)
            
        if course.target_audience:
            course.target_audience_vi = translate_list(course.target_audience)
            
        course.save()
        print(f"Updated Course: {course.title[:30]}... -> {course.title_vi[:30]}...")

if __name__ == "__main__":
    translate_categories()
    translate_courses()
    print("\nDone!")
