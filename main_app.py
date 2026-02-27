import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
# Importing custom helper functions for DB and AI processing
from database_helper import get_db_connection, save_analysis_result, get_user_analysis_history
from processor import extract_text_from_pdf, calculate_match_score, find_missing_skills

# 1. Page Configuration for a professional look
st.set_page_config(page_title="AI Resume Analyzer", layout="wide")

# 2. Initialize Session State for Login Management
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

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


# Helper: Function to generate Excel for Download
def generate_excel(resume_name, score, missing_skills):
    output = BytesIO()
    # Preparing data into a structured format for Excel export
    df_data = pd.DataFrame([{
        "Resume Name": resume_name,
        "Match Score": f"{score}%",
        "Missing Skills": ", ".join(missing_skills)
    }])
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_data.to_excel(writer, index=False, sheet_name='Analysis')
    return output.getvalue()


# Helper: Function to generate PDF for Download
def generate_pdf(resume_name, score, missing_skills):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, "Detailed Resume Analysis Report")

    p.setFont("Helvetica", 12)
    p.drawString(100, 720, f"Candidate Name: {st.session_state['username']}")
    p.drawString(100, 700, f"Target Resume: {resume_name}")
    p.drawString(100, 680, f"Semantic Match Score: {score}%")

    p.drawString(100, 650, "Skill Gaps Identified (Keywords Missing):")
    y_pos = 630
    for skill in missing_skills:
        p.drawString(120, y_pos, f"• {skill}")
        y_pos -= 20
        if y_pos < 50: break
    p.save()
    return buffer.getvalue()


# --- LOGIN PAGE FUNCTION ---
def login_page():
    st.markdown("<div class='main-title'>AI-Powered Resume Analyzer</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Log in to optimize your career journey or find the best talent</div>",
                unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        email = st.text_input("📧 Email Address")
        password = st.text_input(" Password", type='password')

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("Login"):
                db = get_db_connection()
                if db:
                    cursor = db.cursor(dictionary=True)
                    # Authenticating user credentials and fetching profile details
                    query = "SELECT * FROM users WHERE email = %s AND password = %s"
                    cursor.execute(query, (email, password))
                    user = cursor.fetchone()
                    if user:
                        st.session_state['logged_in'] = True
                        st.session_state['user_role'] = user['user_type']
                        st.session_state['username'] = user['username']
                        st.session_state['user_id'] = user['id']
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
    with st.expander(" How it works? - System Overview", expanded=True):
        col_j, col_r = st.columns(2)
        with col_j:
            st.info("###  For Job Seekers")
            st.markdown(
                "<div class='step-box'><b>1. Upload Resume:</b> Upload your PDF.<br><b>2. Paste JD:</b> Enter job vacancy details.<br><b>3. Get Score:</b> AI shows how well you match.</div>",
                unsafe_allow_html=True)
        with col_r:
            st.success("###  For Recruiters")
            st.markdown(
                "<div class='step-box'><b>1. Bulk Upload:</b> Upload many resumes.<br><b>2. Set Target JD:</b> Enter vacancy details.<br><b>3. Rank:</b> System lists top candidates automatically.</div>",
                unsafe_allow_html=True)


# --- REGISTER PAGE FUNCTION ---
def register_page():
    st.title(" Register Your Account")
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


def job_seeker_dashboard():
    st.sidebar.title(f" {st.session_state['username']}")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    st.title(" Job Seeker Dashboard")
    st.write("Analyze your resume and identify skill gaps using SBERT Technology.")

    col1, col2 = st.columns(2)
    with col1:
        uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
    with col2:
        jd_text = st.text_area("Paste Job Description (JD) here...", height=200)

    if st.button("Analyze Resume"):
        if uploaded_file and jd_text:
            with st.spinner("AI is analyzing your profile semantics..."):
                # 1. Processing PDF and calculating semantic similarity
                resume_text = extract_text_from_pdf(uploaded_file)
                score = calculate_match_score(resume_text, jd_text)
                missing = find_missing_skills(resume_text, jd_text)

                # 2. Saving results to the database for persistence
                user_id = st.session_state.get('user_id')
                save_success = save_analysis_result(user_id, uploaded_file.name, jd_text, score, missing)

                if save_success:
                    st.success("Analysis complete! See your detailed results below.")

                    # Result Grid Layout for immediate feedback
                    result_data = {
                        "Feature": ["Resume Name", "Match Score", "Status"],
                        "Details": [
                            uploaded_file.name,
                            f"{score}%",
                            "High Match" if score >= 70 else "Needs Optimization"
                        ]
                    }
                    st.table(result_data)

                    st.subheader(" Skill Gap Analysis")
                    if missing:
                        st.info("The following keywords were found in the JD but are missing from your Resume:")
                        for skill in missing:
                            st.write(f"-  **Suggested Skill to add:** {skill}")
                    else:
                        st.success("Excellent! Your resume covers all major keywords in the JD.")

                    if score >= 70:
                        st.balloons()

                    # --- Report Download Section ---
                    st.write("---")
                    st.subheader(" Download Analysis Results")
                    d_col1, d_col2 = st.columns(2)
                    with d_col1:
                        pdf_data = generate_pdf(uploaded_file.name, score, missing)
                        st.download_button("Download Report (PDF)", pdf_data, f"Report_{uploaded_file.name}.pdf",
                                           "application/pdf")
                    with d_col2:
                        excel_data = generate_excel(uploaded_file.name, score, missing)
                        st.download_button("Export Data (Excel)", excel_data, f"Data_{uploaded_file.name}.xlsx",
                                           "application/vnd.ms-excel")
                else:
                    st.error("Error: Failed to save results to database.")
        else:
            st.warning("Please upload a resume and paste the JD first.")

    # --- VIEW HISTORY SECTION ---
    st.markdown("---")
    st.subheader(" Your Analysis History")
    user_id = st.session_state.get('user_id')
    history = get_user_analysis_history(user_id)

    if history:
        st.write("Review your previous resume analysis records:")
        # Headers for structured history view
        cols = st.columns([2, 1, 3])
        cols[0].write("**Resume Name**")
        cols[1].write("**Match Score**")
        cols[2].write("**Missing Skills**")

        for record in history:
            c1, c2, c3 = st.columns([2, 1, 3])
            c1.info(record['resume_name'])
            c2.success(f"{record['match_score']}%")
            c3.write(record['missing_skills'] if record['missing_skills'] else "Optimized Profile")
    else:
        st.info("No history found. Start analyzing to track your progress!")


# --- RECRUITER DASHBOARD ---
def recruiter_dashboard():
    st.sidebar.title(f" {st.session_state['username']}")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    st.title(" Recruiter Dashboard - Bulk Ranking")
    st.write("Rank multiple resumes based on a specific job vacancy.")

    jd_input = st.text_area("Enter Job Vacancy Description (JD)", height=150)
    uploaded_files = st.file_uploader("Upload Resumes (Max 100 files)", accept_multiple_files=True, type=["pdf"])

    if st.button("Rank Candidates"):
        if uploaded_files and jd_input:
            results = []
            progress_bar = st.progress(0)
            with st.spinner(f"Ranking {len(uploaded_files)} resumes..."):
                for i, file in enumerate(uploaded_files):
                    # Batch processing using SBERT semantic matching
                    text = extract_text_from_pdf(file)
                    score = calculate_match_score(text, jd_input)
                    results.append({"Candidate": file.name, "Match Score (%)": score})
                    progress_bar.progress((i + 1) / len(uploaded_files))

            # Sorting candidates by score in descending order
            sorted_results = sorted(results, key=lambda x: x['Match Score (%)'], reverse=True)
            st.success(f"Ranking complete for {len(uploaded_files)} candidates!")
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