import fitz  # PyMuPDF: Library for PDF text extraction
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# 1. Loading the SBERT Model
# Using 'all-MiniLM-L6-v2' - a lightweight and high-speed model for semantic embeddings.
# This model converts text into numerical vectors representing contextual meaning.
model = SentenceTransformer('all-MiniLM-L6-v2')


def extract_text_from_pdf(pdf_file):
    """
    Extracts all unstructured text from a given PDF file object.
    This is used for reading resumes uploaded by the user.
    """
    try:
        # Open the PDF from the uploaded byte stream
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text = ""
        # Iterate through each page to aggregate all text content
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        return f"Error reading PDF: {e}"


def calculate_match_score(resume_text, jd_text):
    """
    Calculates the semantic similarity between the Resume and Job Description (JD).
    Uses SBERT embeddings and Cosine Similarity for the comparison.
    """
    if not resume_text or not jd_text:
        return 0.0

    # Convert text inputs into numerical vectors (Embeddings)
    #
    embeddings = model.encode([resume_text, jd_text])

    # Apply Cosine Similarity to find the degree of alignment between the two vectors
    similarity = cosine_similarity([embeddings[0]], [embeddings[1]])

    # Convert result to percentage and round to 2 decimal places
    score = round(float(similarity[0][0]) * 100, 2)
    return score