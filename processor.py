import fitz  # PyMuPDF: Handling PDF text extraction
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Initialize SBERT model for Semantic Analysis
# Model: all-MiniLM-L6-v2 (Efficient for real-time sentence embeddings)
model = SentenceTransformer('all-MiniLM-L6-v2')

def extract_text_from_pdf(pdf_file):
    """
    Reads the uploaded PDF file and converts it into plain text.
    Processing step: Iterates through each page and cleans the text.
    """
    try:
        # Stream the file content directly into fitz
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text_content = ""
        for page in doc:
            text_content += page.get_text()
        doc.close()
        return text_content
    except Exception as error:
        return f"Extraction Error: {error}"

def calculate_match_score(resume_text, jd_text):
    """
    Compares Resume content with Job Description using Vector Space Modeling.
    Algorithm: SBERT Embeddings + Cosine Similarity.
    """
    if not resume_text or not jd_text:
        return 0.0

    # Encoding text into high-dimensional numerical vectors
    text_vectors = model.encode([resume_text, jd_text])

    # Calculating the mathematical similarity between the two vectors
    match_calculation = cosine_similarity([text_vectors[0]], [text_vectors[1]])

    # Format result as a percentage for the UI
    final_score = round(float(match_calculation[0][0]) * 100, 2)
    return final_score

def find_missing_skills(resume_text, jd_text):
    """
    Performs a keyword gap analysis to find missing requirements.
    Logic: Uses set difference (JD Keywords - Resume Keywords).
    """
    # Text Normalization: converting to lowercase and tokenizing
    resume_tokens = set(resume_text.lower().split())
    jd_tokens = set(jd_text.lower().split())

    # Identify tokens present in JD but absent in Resume
    missing_elements = jd_tokens - resume_tokens

    # Returning top 10 relevant keywords for optimization
    return list(missing_elements)[:10]