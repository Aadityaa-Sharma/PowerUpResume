import pdfplumber
import random
import re
import os
import time
import requests
import json
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient
from transformers import T5ForConditionalGeneration, T5Tokenizer
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

# ==== AZURE CONFIGURATION - EDIT THESE 2 LINES ====
AZURE_LANGUAGE_KEY = "9xUwVPHnAsGn66eSseCmEjAMfJeRjHpYXZAlxpDDB1SY0RcuVwozJQQJ99BDACGhslBXJ3w3AAAaACOGv4Y9"
AZURE_LANGUAGE_ENDPOINT = "https://powerupresume.cognitiveservices.azure.com/"
# ==== END OF EDITABLE SECTION ====

# Initialize Azure Text Analytics Client
text_analytics_client = TextAnalyticsClient(
    endpoint=AZURE_LANGUAGE_ENDPOINT,
    credential=AzureKeyCredential(AZURE_LANGUAGE_KEY)
)

# 1. Action Verbs List - Categorized for better matching
action_verbs = {
    'achievement': ["Achieved", "Accelerated", "Attained", "Increased", "Improved", "Reduced", "Decreased", "Eliminated", "Won", "Delivered"],
    'leadership': ["Led", "Managed", "Directed", "Supervised", "Headed", "Coordinated", "Administered", "Oversaw", "Guided"],
    'creation': ["Created", "Designed", "Developed", "Engineered", "Built", "Established", "Founded", "Initiated", "Launched", "Pioneered"],
    'analysis': ["Analyzed", "Evaluated", "Researched", "Assessed", "Calculated", "Examined", "Investigated", "Measured", "Quantified"],
    'implementation': ["Implemented", "Executed", "Conducted", "Performed", "Produced", "Completed", "Operated", "Maintained"],
    'innovation': ["Innovated", "Revamped", "Restructured", "Reengineered", "Redesigned", "Transformed", "Reorganized"],
    'technical': ["Programmed", "Coded", "Architected", "Deployed", "Integrated", "Installed", "Configured", "Automated"]
}

# Flatten verb list for general use
all_action_verbs = []
for category in action_verbs:
    all_action_verbs.extend(action_verbs[category])

# 2. ATS Keywords by Industry/Field
ats_keywords = {
    'software_development': [
        "python", "javascript", "java", "c++", "react", "node.js", "fullstack", "frontend", "backend", 
        "cloud", "aws", "azure", "devops", "agile", "scrum", "git", "ci/cd", "docker", "kubernetes", 
        "microservices", "api", "rest", "graphql", "database", "sql", "nosql", "mongodb"
    ],
    'data_science': [
        "machine learning", "data analysis", "statistical analysis", "python", "r", "pandas", "numpy", 
        "scikit-learn", "tensorflow", "pytorch", "deep learning", "nlp", "computer vision", "big data", 
        "data visualization", "tableau", "power bi", "sql", "hadoop", "spark"
    ],
    'web_development': [
        "html", "css", "javascript", "typescript", "react", "angular", "vue", "node.js", "express", 
        "django", "flask", "ruby on rails", "php", "laravel", "wordpress", "responsive design", 
        "ui/ux", "frontend", "backend", "fullstack", "web accessibility", "seo"
    ],
    'product_management': [
        "product strategy", "roadmap", "user research", "market research", "competitive analysis", 
        "agile", "scrum", "kanban", "product lifecycle", "mvp", "user stories", "backlog", "jira", 
        "product development", "stakeholder management", "kpi", "metrics", "analytics"
    ],
    'ui_ux': [
        "user experience", "user interface", "wireframing", "prototyping", "figma", "sketch", "adobe xd", 
        "user research", "usability testing", "information architecture", "interaction design", 
        "visual design", "responsive design", "accessibility", "user-centered design"
    ],
    'general': [
        "leadership", "teamwork", "communication", "problem-solving", "critical thinking", 
        "project management", "time management", "collaboration", "innovation", "creativity", 
        "analytical", "detail-oriented", "organization", "flexibility", "adaptability"
    ]
}

# 3. Load T5 model for text enhancement
print("Loading T5 model (may take 1-2 minutes)...")
tokenizer = T5Tokenizer.from_pretrained("t5-base", legacy=False)
t5_model = T5ForConditionalGeneration.from_pretrained("t5-base")
print("✅ T5 model loaded successfully!")

# 4. ATS Scoring and Analysis Functions
def detect_resume_field(text):
    """Detect the primary field/industry of the resume"""
    text = text.lower()
    
    field_scores = {}
    for field, keywords in ats_keywords.items():
        score = sum(1 for keyword in keywords if keyword.lower() in text)
        field_scores[field] = score
    
    primary_fields = sorted([(k, v) for k, v in field_scores.items() if k != 'general'], 
                           key=lambda x: x[1], reverse=True)
    
    if not primary_fields or primary_fields[0][1] == 0:
        return ['general']
    
    return [primary_fields[0][0], 'general']

def calculate_ats_score(text, fields):
    """Calculate an ATS compatibility score (0-100)"""
    keyword_score = 0
    action_verb_score = 0
    format_score = 0
    content_score = 0
    
    text_lower = text.lower()
    
    # 1. Keyword matching (40%)
    relevant_keywords = []
    for field in fields:
        relevant_keywords.extend(ats_keywords[field])
    
    unique_keywords = set(relevant_keywords)
    matched_keywords = [kw for kw in unique_keywords if kw in text_lower]
    
    # Fixed calculation with proper min() and max()
    keyword_score = min(len(matched_keywords) / max(len(unique_keywords) * 0.2, 1), 1) * 40
    
    # 2. Action verb usage (20%)
    sentences = [s.strip() for s in re.split(r'[.!?]', text) if s.strip()]
    verb_count = sum(1 for s in sentences if any(
        verb.lower() in [w.lower() for w in s.split()[:2]] 
        for verb in all_action_verbs))
    action_verb_score = min(verb_count / max(len(sentences) * 0.3, 1), 1) * 20
    
    # 3. Format and structure (20%)
    bullet_points = len(re.findall(r'[\•\-\*]', text))
    has_sections = any(sec in text_lower for sec in ['education','experience','skills','projects'])
    has_contact = bool(re.search(r'[\w\.-]+@[\w\.-]+', text))
    
    format_score = (min(bullet_points, 20)/20 * 10) + (10 if has_sections else 0) + (5 if has_contact else 0)
    
    # 4. Content quality (20%)
    word_count = len(text.split())
    avg_sentence_len = word_count/max(len(sentences), 1)
    ideal_length = 8 <= avg_sentence_len <= 20
    has_numbers = bool(re.search(r'\d+%|\d+x|\d+\s*times', text))
    
    content_score = (10 if ideal_length else 5) + (10 if has_numbers else 0)
    
    return round(keyword_score + action_verb_score + format_score + content_score)

def get_ats_improvement_suggestions(text, fields, score):
    """Generate suggestions to improve ATS score"""
    suggestions = []
    text_lower = text.lower()
    
    # Keyword suggestions
    all_field_keywords = [kw for field in fields for kw in ats_keywords[field]]
    missing_keywords = [kw for kw in all_field_keywords if kw not in text_lower]
    if missing_keywords:
        sampled = random.sample(missing_keywords, min(5,len(missing_keywords)))
        suggestions.append(f"Add keywords: {', '.join(sampled)}")
    
    # Action verb suggestions
    sentences = [s.strip() for s in re.split(r'[.!?]', text) if s.strip()]
    no_verb_sentences = [s for s in sentences if not any(
        verb.lower() in [w.lower() for w in s.split()[:2]] 
        for verb in all_action_verbs)]
    if no_verb_sentences:
        suggestions.append("Start bullet points with action verbs")
    
    # Quantification check
    if not re.search(r'\d+%|\d+x|\d+\s*times', text):
        suggestions.append("Add quantifiable achievements with metrics")
    
    # Section check
    missing_sections = [sec for sec in ['education','experience','skills','projects'] 
                      if sec not in text_lower]
    if missing_sections:
        suggestions.append(f"Add missing sections: {', '.join(missing_sections).title()}")
    
    # Formatting suggestions
    if score < 70:
        suggestions.append("Improve formatting with clear headings and spacing")
    
    return suggestions[:5]  # Return top 5 suggestions

# 5. Text Enhancement Functions
def fix_spacing(text):
    """Fix spacing issues in text"""
    fixed = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    fixed = re.sub(r'([.,;:])([^\s])', r'\1 \2', fixed)
    return fixed

def is_bulleted_text(text):
    """Check if text is a bullet point"""
    return any(re.match(p, text) for p in [
        r'^\s*•', r'^\s*-', r'^\s*\*', r'^\s*\d+\.', r'^\s*[\(]?[a-zA-Z][\.\)]'])

def is_section_header(text):
    """Check if text is a section header"""
    return (len(text.split()) <= 4 and 
           (text.isupper() or text.endswith(':') or 
            text.strip() in ['EDUCATION','EXPERIENCE','SKILLS','PROJECTS']))

def get_appropriate_verb(text, fields):
    """Select context-appropriate action verb"""
    text_lower = text.lower()
    if any(w in text_lower for w in ["code","program","develop"]):
        return random.choice(action_verbs['technical'])
    elif any(w in text_lower for w in ["team","manage","lead"]):
        return random.choice(action_verbs['leadership'])
    elif any(w in text_lower for w in ["analyze","research","data"]):
        return random.choice(action_verbs['analysis'])
    return random.choice(all_action_verbs)

def rephrase_text(text, fields):
    """Rephrase text using T5 model"""
    if len(text.split()) < 3 or is_section_header(text):
        return text
        
    clean_text = fix_spacing(text)
    field_hint = ""
    if 'software_development' in fields or 'web_development' in fields:
        field_hint = "technical accomplishment: "
    elif 'data_science' in fields:
        field_hint = "data analysis achievement: "
    
    input_text = f"paraphrase {field_hint}{clean_text} </s>"
    input_ids = tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True)
    
    outputs = t5_model.generate(
        input_ids, 
        max_length=512, 
        num_beams=4, 
        temperature=0.7,
        top_p=0.9,
        do_sample=True
    )
    
    rephrased = tokenizer.decode(outputs[0], skip_special_tokens=True)
    if rephrased and not rephrased[0].isupper():
        rephrased = rephrased[0].upper() + rephrased[1:]
    return rephrased

def enhance_line(text, fields):
    """Enhance a resume line"""
    if not text.strip() or len(text.split()) < 3 or is_section_header(text):
        return text
    
    text = fix_spacing(text)
    bullet_match = re.match(r'^(\s*[•\-\*\d\.\)]+\s*)', text)
    bullet_prefix = bullet_match.group(1) if bullet_match else ""
    content = text[len(bullet_prefix):] if bullet_match else text
    
    enhanced_content = rephrase_text(content, fields) or content
    
    # Add action verb if needed
    if is_bulleted_text(text) and not any(
        verb.lower() in [w.lower() for w in enhanced_content.split()[:1]] 
        for verb in all_action_verbs):
        verb = get_appropriate_verb(enhanced_content, fields)
        words = enhanced_content.split()
        if words:
            words[0] = words[0][0].lower() + words[0][1:] if len(words[0])>1 else words[0].lower()
            enhanced_content = f"{verb} {' '.join(words)}"
    
    return f"{bullet_prefix}{enhanced_content}"

# 6. PDF Processing Functions
def extract_pdf_structure(file_path):
    """Extract structured text from PDF"""
    structured_pages = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            if text := page.extract_text():
                structured_pages.append(text.split('\n'))
    return structured_pages

def extract_pdf_full_text(file_path):
    """Extract full text from PDF"""
    full_text = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            if text := page.extract_text():
                full_text.append(text)
    return "\n".join(full_text)

# 7. Azure Enhanced Functions
def analyze_grammar(text):
    """Analyze grammar using Azure"""
    try:
        response = text_analytics_client.analyze_sentiment(
            documents=[text],
            show_opinion_mining=True
        )
        return {
            'confidence': response[0].confidence_scores,
            'sentiment': response[0].sentiment
        }
    except Exception as e:
        print(f"Azure grammar error: {str(e)}")
        return None

def get_azure_key_phrases(text):
    """Extract key phrases using Azure"""
    try:
        response = text_analytics_client.extract_key_phrases([text])
        return response[0].key_phrases if not response[0].is_error else []
    except Exception as e:
        print(f"Azure key phrase error: {str(e)}")
        return []

def generate_smart_suggestions(text, fields):
    """Generate AI-powered suggestions"""
    suggestions = []
    
    try:
        # Azure-based suggestions
        phrases = get_azure_key_phrases(text)
        missing = [kw for field in fields for kw in ats_keywords[field] if kw not in phrases]
        if missing:
            suggestions.append(f"Add key phrases: {', '.join(missing[:3])}")
        
        grammar = analyze_grammar(text)
        if grammar and grammar['sentiment'] == 'negative':
            suggestions.append("Improve positive language")
    
    except Exception as e:
        print(f"Azure suggestion error: {str(e)}")
    
    # Local suggestions
    local_suggestions = get_ats_improvement_suggestions(text, fields, 0)
    suggestions.extend(local_suggestions)
    
    return list(set(suggestions))[:5]  # Remove duplicates

# 8. Main Processing Function
def process_resume(pdf_path, output_pdf_path):
    """Process resume with enhanced analysis"""
    print("\n🔍 Analyzing resume structure...")
    full_text = extract_pdf_full_text(pdf_path)
    
    # Detect resume field
    fields = detect_resume_field(full_text)
    print(f"Detected fields: {', '.join(fields)}")
    
    # Calculate scores
    initial_score = calculate_ats_score(full_text, fields)
    enhanced_score = initial_score  # Initialize
    
    # Get suggestions
    suggestions = generate_smart_suggestions(full_text, fields)
    
    # Enhance content
    print("\n🔧 Enhancing resume content...")
    structured_pages = extract_pdf_structure(pdf_path)
    enhanced_pages = []
    for page in structured_pages:
        enhanced_page = [enhance_line(line, fields) for line in page]
        enhanced_pages.append(enhanced_page)
    
    # Recalculate enhanced score
    enhanced_text = "\n".join(["\n".join(p) for p in enhanced_pages])
    enhanced_score = calculate_ats_score(enhanced_text, fields)
    
    # Generate PDF report
    create_pdf_document(
        enhanced_pages, 
        output_pdf_path,
        initial_score,
        enhanced_score,
        fields,
        suggestions
    )
    
    print(f"\n✅ Enhanced resume saved to: {os.path.abspath(output_pdf_path)}")
    print(f"📈 Score improved from {initial_score} → {enhanced_score}")

# 9. PDF Generation (Fixed Style Handling)
def create_pdf_document(pages, output_path, initial_score, enhanced_score, fields, suggestions):
    """Generate ATS-optimized PDF with proper style management"""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    
    # Create fresh styles to avoid conflicts
    styles = getSampleStyleSheet()
    custom_styles = {
        'Header1': ParagraphStyle(
            name='Header1',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=14,
            spaceAfter=12
        ),
        'BodyText': ParagraphStyle(
            name='BodyText',
            parent=styles['BodyText'],
            fontName='Helvetica',
            fontSize=10,
            spaceAfter=6
        ),
        'BulletPoint': ParagraphStyle(
            name='BulletPoint',
            parent=styles['BodyText'],
            fontName='Helvetica',
            fontSize=10,
            leftIndent=20
        )
    }
    
    content = []
    
    # ATS Report Section
    content.append(Paragraph("ATS OPTIMIZATION REPORT", custom_styles['Header1']))
    content.append(Spacer(1, 0.2*inch))
    
    # Score Table
    data = [
        ["Metric", "Original", "Enhanced"],
        ["ATS Score", str(initial_score), str(enhanced_score)],
        ["Detected Fields", ", ".join(f.replace('_',' ').title() for f in fields), ""]
    ]
    table = Table(data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    content.append(table)
    content.append(Spacer(1, 0.3*inch))
    
    # Suggestions
    content.append(Paragraph("Improvement Suggestions:", custom_styles['Header1']))
    for sug in suggestions:
        content.append(Paragraph(f"• {sug}", custom_styles['BulletPoint']))
    content.append(Spacer(1, 0.3*inch))
    
    # Enhanced Resume Content
    content.append(Paragraph("ENHANCED RESUME CONTENT", custom_styles['Header1']))
    for page in pages:
        for line in page:
            if is_section_header(line):
                content.append(Paragraph(line, custom_styles['Header1']))
            elif is_bulleted_text(line):
                content.append(Paragraph(line, custom_styles['BulletPoint']))
            else:
                content.append(Paragraph(line, custom_styles['BodyText']))
        content.append(Spacer(1, 0.2*inch))
    
    doc.build(content)

# 10. Main Function
def main(input_pdf="resume.pdf", output_pdf="enhanced_resume.pdf"):
    """Main entry point"""
    start_time = time.time()
    
    if not os.path.exists(input_pdf):
        print(f"❌ Error: Input file {input_pdf} not found!")
        return
    
    process_resume(input_pdf, output_pdf)
    
    print(f"\n⏱️  Total processing time: {time.time()-start_time:.2f}s")

if __name__ == "__main__":
    # Verify Azure configuration
    if "your-azure-key-here" in [AZURE_LANGUAGE_KEY, AZURE_LANGUAGE_ENDPOINT]:
        print("\n⚠️  Azure features disabled - using local analysis only")
        print("   Replace placeholder values in lines 24-25 to enable Azure integration")
    
    main("Aryan_CV_LINKEDIN.pdf", "Aryan_CV_Enhanced.pdf")