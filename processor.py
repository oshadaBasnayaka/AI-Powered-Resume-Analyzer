import fitz  # PyMuPDF: Standard library for extracting raw text from document streams
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re  # Used for regex-based text tokenization and cleaning

# Global Initialization of the SBERT Engine
# We use 'all-MiniLM-L6-v2' because it provides a good balance between speed and semantic accuracy
# Unlike standard keyword matching, this model captures the contextual meaning of phrases
model = SentenceTransformer('all-MiniLM-L6-v2')

def extract_text_from_pdf(pdf_file):
    """
    Core NLP Module: Resume Parser
    Handles the initial data extraction layer. It converts unstructured PDF bytes into
    normalized plain text to be consumed by the analysis models.
    """
    try:
        # Directly reading from the uploaded file stream
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text_content = ""
        # Iterating through pages to aggregate the full document content
        for page in doc:
            text_content += page.get_text()
        doc.close()

        # Whitespace normalization to ensure clean tokenization in later stages
        cleaned_text = " ".join(text_content.split())
        return cleaned_text
    except Exception as error:
        return f"Extraction Error: {error}"

def calculate_match_score(resume_text, jd_text):
    """
    Module: Comparative Analysis Model (ML Tier)
    Calculates a semantic similarity percentage between the candidate's profile and the JD.
    """
    if not resume_text or not jd_text:
        return 0.0

    # Transformation: Converting text into high-dimensional numerical vectors (embeddings)
    # This allows the system to understand that different words can have similar meanings
    text_vectors = model.encode([resume_text, jd_text])

    # Applying Cosine Similarity to measure the distance between the two semantic vectors
    # This identifies overlaps in experience even if the exact terminology differs
    match_calculation = cosine_similarity([text_vectors[0]], [text_vectors[1]])

    # Converting the raw similarity coefficient into a user-friendly percentage
    final_score = round(float(match_calculation[0][0]) * 100, 2)
    return final_score

def find_missing_skills(resume_text, jd_text):
    """
    Module: Skill Gap Identification
    This function dissects the JD to find critical requirements that are absent
    from the candidate's resume.
    """
    # Normalization: Standardizing text to lowercase and stripping punctuation
    # We use a set-based comparison to identify unique word differences
    resume_tokens = set(re.findall(r'\w+', resume_text.lower()))
    jd_tokens = set(re.findall(r'\w+', jd_text.lower()))

    # Logical Operation: Finding tokens unique to the Job Description
    missing_elements = jd_tokens - resume_tokens

    # Noise Reduction: Filtering out standard English stop words to isolate technical skills
    stop_words = {'and', 'the', 'with', 'for', 'from', 'this', 'that', 'should', 'have', 'must'}
    refined_gaps = [word for word in missing_elements if word not in stop_words and len(word) > 2]

    # Returning the most relevant identified gaps for the feedback report
    return list(refined_gaps)[:10]