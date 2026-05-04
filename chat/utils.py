from course.models import CourseResource
import os

def extract_text_from_resource(resource: CourseResource) -> str:
    """
    Safely extracts text from a CourseResource file if it is a supported type (PDF or TXT).
    """
    if not resource.file:
        return ""
        
    file_path = resource.file.path
    if not os.path.exists(file_path):
        return ""
        
    ext = os.path.splitext(file_path)[1].lower()
    
    extracted_text = ""
    
    try:
        # Handle Text files
        if ext == '.txt' or 'text' in resource.file_type.lower():
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                extracted_text = f.read()
                
        # Handle PDF files
        elif ext == '.pdf' or 'pdf' in resource.file_type.lower():
            try:
                import PyPDF2  # type: ignore
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    total_pages = len(reader.pages)
                    
                    text_chunks = []
                    for i in range(total_pages):
                        page = reader.pages[i]
                        text = page.extract_text()
                        if text:
                            text_chunks.append(text)
                            
                    extracted_text = "\n".join(text_chunks)
            except ImportError:
                return "[Error: PyPDF2 is not installed, cannot read PDF attached to lecture.]"
    except Exception as e:
        print(f"Failed to read resource {resource.id}: {e}")
        return f"[Error: Failed to read file {resource.title}]"
        
    return extracted_text
