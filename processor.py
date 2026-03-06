import fitz  # PyMuPDF: Standard library for extracting raw text from document streams
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re

# Load the SBERT model globally so we don't reload it on every request.
# 'all-MiniLM-L6-v2' is fast and lightweight but still highly accurate for semantic matching.
model = SentenceTransformer('all-MiniLM-L6-v2')


def extract_text_from_pdf(pdf_file):
    """
    Reads an uploaded PDF file stream and extracts all the text.
    Normalizes whitespace to make it easier to process later.
    """
    try:
        # Read directly from the Streamlit uploaded file buffer
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text_content = ""

        # Grab text from every page
        for page in doc:
            text_content += page.get_text()
        doc.close()

        # Clean up extra spaces, tabs, and newlines
        cleaned_text = " ".join(text_content.split())
        return cleaned_text
    except Exception as error:
        return f"Extraction Error: {error}"


def calculate_match_score(resume_text, jd_text):
    """
    Compares the resume and job description using SBERT embeddings.
    Returns a match score out of 100%.
    """
    if not resume_text or not jd_text:
        return 0.0

    # Convert both texts into numerical embeddings
    text_vectors = model.encode([resume_text, jd_text])

    # Calculate how close the two vectors are (Cosine Similarity)
    # This catches related skills even if the exact keywords don't match
    match_calculation = cosine_similarity([text_vectors[0]], [text_vectors[1]])

    # Convert the raw similarity score (0 to 1) into a clean percentage
    final_score = round(float(match_calculation[0][0]) * 100, 2)
    return final_score


def find_missing_skills(resume_text, jd_text):
    """
    A simple set-based approach to find words that are in the JD but missing from the resume.
    Useful for quick keyword gap analysis.
    """
    # Convert to lowercase and split into individual words
    resume_tokens = set(re.findall(r'\w+', resume_text.lower()))
    jd_tokens = set(re.findall(r'\w+', jd_text.lower()))

    # Find what's in the JD that isn't in the resume
    missing_elements = jd_tokens - resume_tokens

    # Basic stop word filtering to remove noise.
    # (Note: In a larger production app, spaCy would handle this better)
    stop_words = {'and', 'the', 'with', 'for', 'from', 'this', 'that', 'should', 'have', 'must'}
    refined_gaps = [word for word in missing_elements if word not in stop_words and len(word) > 2]

    # Return up to 10 missing keywords for the feedback report
    return list(refined_gaps)[:10]