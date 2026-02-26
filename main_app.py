import streamlit as st
from database_helper import get_db_connection
# Importing the AI logic from your processor file
from processor import extract_text_from_pdf, calculate_match_score

# Page Configuration
st.set_page_config(page_title="AI Resume Analyzer", page_icon="🚀", layout="wide")

# Initialize Session State
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None

# Custom CSS for Modern Look
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #007bff; color: white; height: 3em; }
    .main-title { font-size: 40px; font-weight: bold; color: #1e293b; text-align: center; }
    .sub-title { font-size: 18px; color: #64748b; text-align: center; margin-bottom: 20px; }
    .step-box { background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 5px solid #007bff; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); min-height: 150px; }
    </style>
    """, unsafe_allow_html=True)


# --- LOGIN PAGE ---
def login_page():
    st.markdown("<div class='main-title'>AI-Powered Resume Analyzer</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Log in to optimize your career journey or find the best talent</div>",
                unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        email = st.text_input("📧 Email Address")
        password = st.text_input("🔒 Password", type='password')

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("Login"):
                db = get_db_connection()
                cursor = db.cursor(dictionary=True)
                query = "SELECT * FROM users WHERE email = %s AND password = %s"
                cursor.execute(query, (email, password))
                user = cursor.fetchone()
                if user:
                    st.session_state['logged_in'] = True
                    st.session_state['user_role'] = user['user_type']
                    st.session_state['username'] = user['username']
                    st.rerun()
                else:
                    st.error("Invalid credentials!")
                cursor.close()
                db.close()
        with btn_col2:
            if st.button("New here? Register"):
                st.session_state['register_mode'] = True
                st.rerun()

    st.markdown("---")

    # GUIDELINE SECTION
    with st.expander("🚀 How it works? - System Overview", expanded=True):
        col_j, col_r = st.columns(2)
        with col_j:
            st.info("### 👨‍💼 For Job Seekers")
            st.markdown(
                "<div class='step-box'><b>1. Upload Resume:</b> Upload your PDF.<br><b>2. Paste JD:</b> Enter the job vacancy details.<br><b>3. Get Score:</b> AI (SBERT) shows how well you match the role.</div>",
                unsafe_allow_html=True)
        with col_r:
            st.success("### 🏢 For Recruiters")
            st.markdown(
                "<div class='step-box'><b>1. Bulk Upload:</b> Upload 50-100 resumes at once.<br><b>2. Set Target JD:</b> Enter the company vacancy.<br><b>3. Rank:</b> System automatically lists top candidates.</div>",
                unsafe_allow_html=True)


# --- REGISTER PAGE ---
def register_page():
    st.title("📝 Register Your Account")
    new_user = st.text_input("Username")
    new_email = st.text_input("Email")
    new_password = st.text_input("Password", type='password')
    role = st.selectbox("I am a:", ["Job Seeker", "Recruiter"])

    if st.button("Create Account"):
        db = get_db_connection()
        cursor = db.cursor()
        query = "INSERT INTO users (username, email, password, user_type) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (new_user, new_email, new_password, role))
        db.commit()
        st.success("Registration successful! Please login.")
        st.session_state['register_mode'] = False
        st.rerun()


