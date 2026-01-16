import docx # type: ignore
import re

def parse_word_file(file_obj):
    """
    Parses a .docx file object and returns a list of dictionaries.
    
    Expected format:
    1. Question text...
       a. Choice 1
       b. Choice 2 (Bold or Red or marked *)
    
    Returns:
    [
        {
            "content": "Question content",
            "choices": [
                {"text": "Choice 1", "correct": False},
                {"text": "Choice 2", "correct": True},
            ]
        },
        ...
    ]
    """
    document = docx.Document(file_obj)
    
    questions = []
    current_question = None
    
    # Regex patterns
    # Question: starts with number + dot/paren (e.g. "1.", "1)", "01.")
    question_pattern = re.compile(r'^\s*\d+[\.\)]\s+(.+)')
    # Choice: starts with letter + dot/paren (e.g. "a.", "A)", "a)")
    choice_pattern = re.compile(r'^\s*[a-zA-Z][\.\)]\s+(.+)')
    
    for para in document.paragraphs:
        text = para.text.strip()
        if not text:
            continue
            
        # Check for Question
        q_match = question_pattern.match(text)
        if q_match:
            # Save previous question if exists
            if current_question:
                questions.append(current_question)
            
            # Start new question
            current_question = {
                "content": q_match.group(1),
                "choices": []
            }
            continue
            
        # Check for Choice
        c_match = choice_pattern.match(text)
        if c_match and current_question:
            choice_text = c_match.group(1)
            is_correct = False
            
            # 1. Check for bolding in runs
            # A paragraph is correct if ANY run in it is bold, BUT we must be careful.
            # Usually the whole line is bolded, or at least the choice text.
            for run in para.runs:
                if run.bold:
                    is_correct = True
                    break
                    
                # 2. Check for Red color (RGB FF0000 or pre-defined red index)
                # This is trickier in python-docx, focusing on Bold first as requested.
                if run.font.color and run.font.color.rgb == docx.shared.RGBColor(255, 0, 0):
                     is_correct = True
                     break
            
            # 3. Check for asterisk prefix as fallback "*a. Answer" (if parser didn't strip it yet, relying on pattern)
            # If our regex matched "a. *Answer"
            if choice_text.startswith('*'):
                is_correct = True
                choice_text = choice_text[1:].strip()
                
            current_question["choices"].append({
                "text": choice_text,
                "correct": is_correct
            })
            continue
            
        # If line is continuation of question or choice (multiline), handling simple case:
        # Append to last choice or question content?
        # For simplicity, ignoring or assuming single line for now.
        
    # Append last question
    if current_question:
        questions.append(current_question)
        
    return questions
