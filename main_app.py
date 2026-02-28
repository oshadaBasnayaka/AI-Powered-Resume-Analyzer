import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import plotly.express as px  # Professional visualization for Recruiter

# Link to custom logic for DB interactions and AI processing
from database_helper import (
    get_db_connection,
    save_analysis_to_db,
    fetch_user_history,
    save_full_shortlist,
    fetch_recruiter_shortlists
)
from processor import extract_text_from_pdf, calculate_match_score, find_missing_skills

# Global application configuration
st.set_page_config(page_title="AI Resume Analyzer", layout="wide")

# Persistent session state to manage user authentication and roles
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None

# Custom CSS for branding and standardizing component spacing
st.markdown("""
<style>
.main { background-color: #f8f9fa; }
.stButton>button { width: 100%; border-radius: 5px; background-color: #007bff; color: white; height: 3em; }
.main-title { font-size: 40px; font-weight: bold; color: #1e293b; text-align: center; }
.sub-title { font-size: 18px; color: #64748b; text-align: center; margin-bottom: 20px; }
.step-box { background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 5px solid #007bff; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); min-height: 150px; }
</style>
""", unsafe_allow_html=True)


# --- EXPORT HELPERS ---

def generate_excel(resume_name, score, missing_skills):
    """Converts raw analysis results into a structured Excel buffer for download."""
    output = BytesIO()
    df_data = pd.DataFrame([{
        "Resume Name": resume_name,
        "Match Score": f"{score}%",
        "Missing Skills": ", ".join(missing_skills)
    }])
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_data.to_excel(writer, index=False, sheet_name='Analysis')
    return output.getvalue()


def generate_pdf(resume_name, score, missing_skills):
    """Generates a formal PDF report using canvas coordinates for layout control."""
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


# --- AUTHENTICATION FLOWS ---

def login_page():
    """Handles user entry and redirects based on account types."""
    st.markdown("<div class='main-title'>AI-Powered Resume Analyzer</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Log in to optimize your career journey or find the best talent</div>",
                unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        email = st.text_input("Email Address")
        password = st.text_input("Password", type='password')
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("Login"):
                db = get_db_connection()
                if db:
                    cursor = db.cursor(dictionary=True)
                    # Cross-reference credentials with User table
                    query = "SELECT * FROM users WHERE email = %s AND password_hash = %s"
                    cursor.execute(query, (email, password))
                    user = cursor.fetchone()
                    if user:
                        # Set session context for authorized access
                        st.session_state.update({
                            'logged_in': True,
                            'user_role': user['user_role'],
                            'username': user['full_name'],
                            'user_id': user['id']
                        })
                        st.rerun()
                    else:
                        st.error("Invalid credentials!")
                    db.close()
        with btn_col2:
            if st.button("New here? Register"):
                st.session_state['register_mode'] = True
                st.rerun()
    st.markdown("---")
    # Quick onboarding guide for new users
    with st.expander("ℹ How it works? - System Overview", expanded=True):
        col_j, col_r = st.columns(2)
        with col_j:
            st.info("### For Job Seekers")
            st.markdown(
                "<div class='step-box'><b>1. Upload Resume:</b> Upload your PDF.<br><b>2. Paste JD:</b> Enter job vacancy details.<br><b>3. Get Score:</b> AI shows how well you match.</div>",
                unsafe_allow_html=True)
        with col_r:
            st.success("### For Recruiters")
            st.markdown(
                "<div class='step-box'><b>1. Bulk Upload:</b> Upload many resumes.<br><b>2. Set Target JD:</b> Enter vacancy details.<br><b>3. Rank:</b> System lists top candidates automatically.</div>",
                unsafe_allow_html=True)


def register_page():
    """Captures new user data to create role-specific profiles."""
    st.title("Register Your Account")
    new_user = st.text_input("Full Name")
    new_email = st.text_input("Email")
    new_password = st.text_input("Password", type='password')
    role = st.selectbox("I am a:", ["Job Seeker", "Recruiter"])
    if st.button("Create Account"):
        db = get_db_connection()
        if db:
            cursor = db.cursor()
            # Direct insertion of profile metadata
            query = "INSERT INTO users (full_name, email, password_hash, user_role) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (new_user, new_email, new_password, role))
            db.commit()
            st.success("Registration successful! Please login.")
            st.session_state['register_mode'] = False
            st.rerun()


# --- USER DASHBOARDS ---

def job_seeker_dashboard():
    """Dashboard for individual candidates to perform self-analysis and gap identification."""
    st.sidebar.title(f" {st.session_state['username']}")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    st.title("Job Seeker Dashboard")
    st.write("Analyze your resume and identify skill gaps using SBERT Technology.")

    col1, col2 = st.columns(2)
    with col1:
        # File upload handling
        uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
    with col2:
        # JD input handling
        jd_text = st.text_area("Paste Job Description (JD) here...", height=200)

    if st.button("Analyze Resume"):
        if uploaded_file and jd_text:
            with st.spinner("AI is analyzing your profile semantics..."):
                # Execution of the NLP processing chain
                resume_text = extract_text_from_pdf(uploaded_file)
                score = calculate_match_score(resume_text, jd_text)  # SBERT comparison
                missing = find_missing_skills(resume_text, jd_text)  # Gap analysis

                u_id = st.session_state['user_id']
                # Saving to the analysis_results junction table for history tracking
                if save_analysis_to_db(u_id, uploaded_file.name, jd_text, score, missing):
                    st.success("Analysis complete and synced with your database!")

                    # Instant feedback display via a results grid
                    result_data = {"Feature": ["Resume Name", "Match Score", "Status"],
                                   "Details": [uploaded_file.name, f"{score}%",
                                               "High Match" if score >= 70 else "Needs Optimization"]}
                    st.table(result_data)

                    st.subheader("Skill Gap Analysis")
                    if missing:
                        st.info("The following keywords were found in the JD but are missing from your Resume:")
                        for skill in missing: st.write(f"- Suggested Skill to add: {skill}")
                    else:
                        st.success("Excellent! Your resume covers all major keywords in the JD.")

                    if score >= 70: st.balloons()

                    st.write("---")
                    st.subheader("Download Analysis Results")
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
                    st.error("Error: Database sync failed.")
        else:
            st.warning("Please upload a resume and paste the JD first.")

    st.markdown("---")
    st.subheader("Your Analysis History")
    history = fetch_user_history(st.session_state['user_id'])
    if history:
        st.write("Review your previous resume analysis records:")
        cols = st.columns([2, 1, 3])
        cols[0].write("**Resume Name**")
        cols[1].write("**Match Score**")
        cols[2].write("**Missing Skills**")
        for record in history:
            c1, c2, c3 = st.columns([2, 1, 3])
            c1.info(record['file_name'])
            c2.success(f"{record['match_score']}%")
            c3.write(record['skill_gap_analysis'] if record['skill_gap_analysis'] else "Optimized Profile")
    else:
        st.info("No history found. Start analyzing to track your progress!")


def recruiter_dashboard():
    """High-capacity portal for ranking batches of candidates against a target vacancy."""
    st.sidebar.title(f" Recruiter: {st.session_state['username']}")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    st.markdown("<div class='main-title'>Recruiter Ranking Hub</div>", unsafe_allow_html=True)
    st.write("Rank multiple resumes instantly using SBERT Semantic Analysis.")

    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.subheader("Job Vacancy Details")
        target_jd = st.text_area("Enter Company Job Description (JD)", height=200,
                                 placeholder="Paste requirements here...")
    with col_b:
        st.subheader("Candidate Resumes")
        # Batch upload handling for 50-100 files
        bulk_files = st.file_uploader("Upload Resumes (Max 100 PDF files)", accept_multiple_files=True,
                                      type=["pdf"])

    if st.button("Start Bulk Ranking"):
        if bulk_files and target_jd:
            results = []
            p_bar = st.progress(0)
            with st.spinner(f"AI is processing {len(bulk_files)} candidates..."):
                for i, file in enumerate(bulk_files):
                    # Loop for iterative processing of the batch
                    text = extract_text_from_pdf(file)
                    score = calculate_match_score(text, target_jd)
                    results.append({"Candidate": file.name, "Score": score})
                    p_bar.progress((i + 1) / len(bulk_files))

            # Ranking candidates from top match to bottom
            sorted_results = sorted(results, key=lambda x: x['Score'], reverse=True)
            # Store temporary results in session for persistence during save action
            st.session_state['last_ranking_results'] = sorted_results
            st.session_state['last_jd_used'] = target_jd

            df = pd.DataFrame(sorted_results)

            st.write("---")
            st.subheader("Visual Ranking Analysis")
            chart_col, table_col = st.columns([1.5, 1])
            with chart_col:
                # Comparative bar chart via Plotly for visual decision making
                fig = px.bar(df, x='Score', y='Candidate', orientation='h', title="Candidate Match Comparison",
                             color='Score', color_continuous_scale='Blues', text='Score')
                fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=400)
                st.plotly_chart(fig, use_container_width=True)
            with table_col:
                st.write("**Top Candidates Leaderboard**")
                st.dataframe(df, use_container_width=True, hide_index=True)

            st.write("---")
            st.subheader("Quick Statistics")
            stat1, stat2, stat3 = st.columns(3)
            stat1.metric("Total Resumes", len(bulk_files))
            stat2.metric("Highest Score", f"{df['Score'].max()}%")
            stat3.metric("Average Match", f"{round(df['Score'].mean(), 2)}%")

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Export Full Ranking (CSV)", csv, "Candidate_Ranking.csv", "text/csv")
        else:
            st.warning("Please provide a Job Description and resumes.")

    # --- SAVE SHORTLIST PROJECT LOGIC ---
    if 'last_ranking_results' in st.session_state:
        st.write("---")
        st.subheader(" Save Shortlist Project")
        shortlist_name = st.text_input("Enter Project Name", placeholder="e.g., Software Engineer ")

        if st.button("Confirm and Save Shortlist"):
            if shortlist_name:
                rec_id = st.session_state['user_id']
                jd_val = st.session_state['last_jd_used']
                data_val = st.session_state['last_ranking_results']

                # Committing the ranked list to permanent storage
                if save_full_shortlist(rec_id, jd_val, shortlist_name, data_val):
                    st.success(f"Shortlist '{shortlist_name}' saved successfully!")
                    st.rerun()
            else:
                st.warning("Please enter a project name.")

    # --- HISTORY VIEW FOR SAVED HIRING PROJECTS ---
    st.write("---")
    st.subheader("Saved Shortlists")

    recruiter_id = st.session_state.get('user_id')
    saved_shortlists = fetch_recruiter_shortlists(recruiter_id)

    if saved_shortlists:
        for slist in saved_shortlists:
            # Displaying each hiring project within an expandable section
            with st.expander(f" {slist['title']} (For: {slist['job_title']})"):
                st.write(f"Shortlist ID: {slist['id']} | Created: {slist['created_at']}")

                # Dynamically fetching the ranked items for the selected shortlist
                db = get_db_connection()
                cur = db.cursor(dictionary=True)
                # Query using backticks for Rank to avoid MySQL syntax conflicts
                cur.execute("""
                                        SELECT si.rank_order as `Rank`, 
                                               r.file_name as Candidate, 
                                               ar.match_score as `AI Score`
                                        FROM shortlist_items si
                                        JOIN resumes r ON si.resume_id = r.id
                                        JOIN analysis_results ar ON si.analysis_result_id = ar.id
                                        WHERE si.shortlist_id = %s
                                        ORDER BY si.rank_order ASC
                                    """, (slist['id'],))
                items = cur.fetchall()
                db.close()

                if items:
                    st.dataframe(pd.DataFrame(items), use_container_width=True, hide_index=True)
                else:
                    st.info("No candidates in this shortlist.")
    else:
        st.info("No shortlists created yet. Rank candidates to start.")


# --- MAIN ROUTING LOGIC ---
if not st.session_state['logged_in']:
    if st.session_state.get('register_mode', False):
        register_page()
    else:
        login_page()
else:
    # Dashboard redirect based on account user_role
    if st.session_state['user_role'] == "Job Seeker":
        job_seeker_dashboard()
    else:
        recruiter_dashboard()