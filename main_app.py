import streamlit as st
# Importing our custom helper functions from your files
from database_helper import get_db_connection
from processor import extract_text_from_pdf, calculate_match_score

# 1. Page Configuration for a professional look
st.set_page_config(page_title="AI Resume Analyzer", page_icon="🚀", layout="wide")

# 2. Initialize Session State for Login Management
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None

# 3. Custom CSS for a modern UI/UX
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #007bff; color: white; height: 3em; }
    .main-title { font-size: 40px; font-weight: bold; color: #1e293b; text-align: center; }
    .sub-title { font-size: 18px; color: #64748b; text-align: center; margin-bottom: 20px; }
    .step-box { background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 5px solid #007bff; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); min-height: 150px; }
    </style>
    """, unsafe_allow_html=True)


# --- LOGIN PAGE FUNCTION ---
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
                if db:
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

    # SYSTEM OVERVIEW (GUIDELINE)
    with st.expander("🚀 How it works? - System Overview", expanded=True):
        col_j, col_r = st.columns(2)
        with col_j:
            st.info("### 👨‍💼 For Job Seekers")
            st.markdown(
                "<div class='step-box'><b>1. Upload Resume:</b> Upload your PDF.<br><b>2. Paste JD:</b> Enter job vacancy details.<br><b>3. Get Score:</b> AI shows how well you match.</div>",
                unsafe_allow_html=True)
        with col_r:
            st.success("### 🏢 For Recruiters")
            st.markdown(
                "<div class='step-box'><b>1. Bulk Upload:</b> Upload many resumes.<br><b>2. Set Target JD:</b> Enter vacancy details.<br><b>3. Rank:</b> System lists top candidates.</div>",
                unsafe_allow_html=True)


# --- REGISTER PAGE FUNCTION ---
def register_page():
    st.title("📝 Register Your Account")
    new_user = st.text_input("Username")
    new_email = st.text_input("Email")
    new_password = st.text_input("Password", type='password')
    role = st.selectbox("I am a:", ["Job Seeker", "Recruiter"])

    if st.button("Create Account"):
        db = get_db_connection()
        if db:
            cursor = db.cursor()
            query = "INSERT INTO users (username, email, password, user_type) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (new_user, new_email, new_password, role))
            db.commit()
            st.success("Registration successful! Please login.")
            st.session_state['register_mode'] = False
            st.rerun()


# --- JOB SEEKER DASHBOARD ---
def job_seeker_dashboard():
    st.sidebar.title(f"👋 {st.session_state['username']}")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    st.title("🎯 Job Seeker Dashboard")
    st.write("Analyze your resume against a specific job description.")

    col1, col2 = st.columns(2)
    with col1:
        uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
    with col2:
        jd_text = st.text_area("Paste Job Description (JD) here...", height=200)

    if st.button("Analyze Resume"):
        if uploaded_file and jd_text:
            with st.spinner("AI is analyzing your resume content..."):
                # Real Extraction and Scoring
                resume_text = extract_text_from_pdf(uploaded_file)
                score = calculate_match_score(resume_text, jd_text)

                st.success("Analysis Complete!")
                st.metric(label="Similarity Match Score", value=f"{score}%")

                if score >= 70:
                    st.balloons()
                    st.write("🔥 **Excellent match!** Your profile aligns well.")
                else:
                    st.warning("💡 **Tip:** Add more keywords from the JD to improve your score.")
        else:
            st.warning("Please upload a resume and paste the JD.")


# --- RECRUITER DASHBOARD ---
def recruiter_dashboard():
    st.sidebar.title(f"🏢 {st.session_state['username']}")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    st.title("🏢 Recruiter Dashboard - Bulk Ranking")
    st.write("Rank multiple resumes based on a job vacancy.")

    jd_input = st.text_area("Enter Job Vacancy Description (JD)", height=150)
    uploaded_files = st.file_uploader("Upload Resumes (Max 100 files)", accept_multiple_files=True, type=["pdf"])

    if st.button("Rank Candidates"):
        if uploaded_files and jd_input:
            results = []
            progress_bar = st.progress(0)
            with st.spinner(f"Ranking {len(uploaded_files)} resumes..."):
                for i, file in enumerate(uploaded_files):
                    text = extract_text_from_pdf(file)
                    score = calculate_match_score(text, jd_input)
                    results.append({"Candidate": file.name, "Match Score (%)": score})
                    progress_bar.progress((i + 1) / len(uploaded_files))

            # Sorting by score (Descending)
            sorted_results = sorted(results, key=lambda x: x['Match Score (%)'], reverse=True)
            st.success("Ranking complete!")
            st.table(sorted_results)
        else:
            st.warning("Please provide JD and upload resumes.")


# --- MAIN LOGIC ---
if not st.session_state['logged_in']:
    if st.session_state.get('register_mode', False):
        register_page()
    else:
        login_page()
else:
    if st.session_state['user_role'] == "Job Seeker":
        job_seeker_dashboard()
    else:
        recruiter_dashboard()