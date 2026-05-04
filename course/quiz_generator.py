import json
import os
import google.generativeai as genai
from django.conf import settings
from tempfile import NamedTemporaryFile

# Try importing libraries, handle missing ones gracefully
try:
    import PyPDF2
    import docx
except ImportError:
    # If not installed, we'll try to auto-install them via subprocess
    import subprocess
    import sys
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyPDF2", "python-docx"])
        import PyPDF2
        import docx
    except Exception as e:
        print(f"Warning: Could not auto-install PyPDF2 and python-docx. Please install manually. {e}")

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def extract_text_from_file(file_obj, filename):
    """
    Extract text from uploaded PDF or Word document
    """
    ext = os.path.splitext(filename)[1].lower()
    text = ""
    
    # We need to save the InMemoryUploadedFile to a temporary file first
    with NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
        for chunk in file_obj.chunks():
            temp_file.write(chunk)
        temp_file_path = temp_file.name

    try:
        if ext == '.pdf':
            with open(temp_file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
        elif ext in ['.docx', '.doc']:
            doc = docx.Document(temp_file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        else:
            # Fallback for txt
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                text = f.read()
    except Exception as e:
        print(f"Error extracting text: {e}")
        raise ValueError(f"Could not extract text from {ext} file. It might be corrupted or unsupported.")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            
    return text.strip()

def generate_quiz_from_text(text, num_questions=10):
    """
    Use Gemini to generate a quiz from text
    Returns a list of dictionaries with question, choices, correct_answer
    """
    # Truncate text if it's too long (Gemini 2.5 has 1M context, but let's keep it reasonable)
    if len(text) > 100000:
        text = text[:100000]
        
    prompt = f"""
    You are an expert educator. Create exactly {num_questions} multiple-choice questions based ONLY on the provided text.
    
    Return the result strictly as a valid JSON array of objects. Do not use markdown formatting (like ```json), just return the raw JSON array.
    Each object must have:
    - "question": string, the question text
    - "choices": array of 4 string choices
    - "correct_answer": string, the exact text of the correct choice from the choices array
    - "explanation": string, a brief explanation of why the answer is correct based on the text.
    
    Source Text:
    {text}
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                response_mime_type="application/json"
            )
        )
        
        # Parse response
        json_text = response.text.strip()
        # Clean up if Gemini returns markdown code blocks despite instructions
        if json_text.startswith("```json"):
            json_text = json_text[7:]
        if json_text.startswith("```"):
            json_text = json_text[3:]
        if json_text.endswith("```"):
            json_text = json_text[:-3]
            
        questions_data = json.loads(json_text.strip())
        
        # Validate structure
        valid_questions = []
        for q in questions_data:
            if all(k in q for k in ["question", "choices", "correct_answer", "explanation"]):
                valid_questions.append(q)
                
        return valid_questions
    except Exception as e:
        print(f"Gemini API Error: {e}")
        raise Exception("Failed to generate quiz with AI. Please try again with a different document.")
