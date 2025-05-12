import openai
import os
from docx import Document
from PyPDF2 import PdfReader
from fpdf import FPDF
import unicodedata

# Initialize the OpenAI client
client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def normalize_text(text):
    """Normalize text to handle special characters"""
    # Convert to ASCII, replacing non-ASCII characters with their closest ASCII equivalent
    return unicodedata.normalize('NFKD', text).encode('ASCII', 'replace').decode('ASCII')

def extract_text_from_file(file):
    ext = file.filename.split(".")[-1]
    if ext == "txt":
        return file.file.read().decode("utf-8")
    elif ext == "pdf":
        pdf = PdfReader(file.file)
        return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
    elif ext == "docx":
        doc = Document(file.file)
        return "\n".join([para.text for para in doc.paragraphs])
    return ""

def create_pdf_report(filename, original_input, summary_text):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Use built-in fonts
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 10, "AI-Generated Business Report", ln=True)
    pdf.ln(5)

    # Input section
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, "Input Provided:", ln=True)
    pdf.set_font("Helvetica", '', 11)
    # Normalize and split text into lines
    input_lines = normalize_text(original_input).split('\n')
    for line in input_lines:
        if line.strip():  # Only add non-empty lines
            pdf.multi_cell(0, 10, line)
    pdf.ln(5)

    # Summary section
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, "AI Summary and Proposal:", ln=True)
    pdf.set_font("Helvetica", '', 11)
    # Normalize and split text into lines
    summary_lines = normalize_text(summary_text).split('\n')
    for line in summary_lines:
        if line.strip():  # Only add non-empty lines
            pdf.multi_cell(0, 10, line)

    # Ensure reports directory exists
    os.makedirs("reports", exist_ok=True)
    path = os.path.join("reports", filename)
    pdf.output(path)
    return path

async def analyze_text(text: str):
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    prompt = f"You are an enterprise solution architect. Given the following input (could be a problem statement, conversation or meeting notes):\n\nYour job is to:\n- Understand and summarize key challenges\n- Extract goals and business needs\n- Propose a strategic business solution\n- (Optional) Provide action items\n\nInput:\n{text}"
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        summary = response.choices[0].message.content
        return {
            "summary": summary,
            "original_input": text
        }
    except Exception as e:
        print(f"OpenAI API Error: {str(e)}")
        raise

async def analyze_uploaded_file(file):
    text = extract_text_from_file(file)
    return await analyze_text(text)

def generate_pdf(original_input, summary_text, filename):
    return create_pdf_report(filename, original_input, summary_text)
