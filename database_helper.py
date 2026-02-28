import mysql.connector


# Centralized connection logic to handle MySQL access
def get_db_connection():
    """
    Main hub for database connectivity.
    Returns a connection object for executing SQL queries.
    """
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="12345",
            database="resume_analyzer_db"
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Database Connection Error: {err}")
        return None


def save_analysis_to_db(user_id, resume_name, jd_text, score, gaps):
    """
    This is the core storage logic for single resume analysis.
    It links the JD and Resume to create a record in the junction table.
    """
    db = get_db_connection()
    if not db: return False
    try:
        cursor = db.cursor()

        # Step 1: Log the Job Description details first
        cursor.execute("INSERT INTO job_descriptions (job_title, jd_content, created_by) VALUES (%s, %s, %s)",
                       ("Analysis Target", jd_text, user_id))
        jd_id = cursor.lastrowid

        # Step 2: Register the resume metadata
        cursor.execute("INSERT INTO resumes (user_id, file_name) VALUES (%s, %s)", (user_id, resume_name))
        res_id = cursor.lastrowid

        # Step 3: Insert the final calculated results into the junction table
        # This maps IDs from JD and Resumes to maintain data integrity
        gaps_str = ", ".join(gaps) if isinstance(gaps, list) else gaps
        cursor.execute(
            "INSERT INTO analysis_results (resume_id, jd_id, user_id, match_score, skill_gap_analysis) VALUES (%s, %s, %s, %s, %s)",
            (res_id, jd_id, user_id, score, gaps_str))

        db.commit()
        return True
    except Exception as e:
        print(f"Storage Error: {e}")
        return False
    finally:
        db.close()


def fetch_user_history(user_id):
    """
    Retrieves the last 10 analysis records for the logged-in user.
    Uses a JOIN to combine metadata with actual AI scores.
    """
    db = get_db_connection()
    if not db: return []
    try:
        cursor = db.cursor(dictionary=True)
        # Pulling filenames and scores through the junction table
        query = "SELECT r.file_name, a.match_score, a.skill_gap_analysis FROM analysis_results a JOIN resumes r ON a.resume_id = r.id WHERE a.user_id = %s ORDER BY a.id DESC LIMIT 10"
        cursor.execute(query, (user_id,))
        return cursor.fetchall()
    finally:
        db.close()


# --- RECRUITER FUNCTIONS ---

def save_full_shortlist(recruiter_id, jd_text, title, candidates_list):
    """
    Handles bulk saving for the Recruiter module.
    Maintains the 1:N relationship between one shortlist project and multiple candidates.
    """
    db = get_db_connection()
    if not db: return False
    try:
        cursor = db.cursor()

        # Step 1: Create the main Job Description entry
        cursor.execute("INSERT INTO job_descriptions (job_title, jd_content, created_by) VALUES (%s, %s, %s)",
                       (title, jd_text, recruiter_id))
        jd_id = cursor.lastrowid

        # Step 2: Create the Shortlist project header
        cursor.execute("INSERT INTO shortlists (recruiter_id, jd_id, title) VALUES (%s, %s, %s)",
                       (recruiter_id, jd_id, title))
        shortlist_id = cursor.lastrowid

        # Step 3: Iteratively save each candidate in the batch
        # Using enumerate to track the loop index for the 'rank_order' field
        for rank, cand in enumerate(candidates_list, start=1):
            # Log individual candidate resume
            cursor.execute("INSERT INTO resumes (user_id, file_name) VALUES (%s, %s)",
                           (recruiter_id, cand['Candidate']))
            res_id = cursor.lastrowid

            # Save the specific analysis results for this candidate
            cursor.execute(
                "INSERT INTO analysis_results (resume_id, jd_id, user_id, match_score) VALUES (%s, %s, %s, %s)",
                (res_id, jd_id, recruiter_id, cand['Score']))
            analysis_id = cursor.lastrowid

            # Map the candidate to the specific shortlist project with their rank
            cursor.execute(
                "INSERT INTO shortlist_items (shortlist_id, resume_id, analysis_result_id, rank_order) VALUES (%s, %s, %s, %s)",
                (shortlist_id, res_id, analysis_id, rank))

        db.commit()
        return True
    finally:
        db.close()


def fetch_recruiter_shortlists(recruiter_id):
    """
    Retrieves all saved hiring projects for a specific recruiter.
    Shows the project title linked with the targeted job vacancy.
    """
    db = get_db_connection()
    if not db: return []
    try:
        cursor = db.cursor(dictionary=True)
        # Combining Shortlist details with Job Titles using JD_ID
        query = "SELECT s.id, s.title, j.job_title, s.created_at FROM shortlists s JOIN job_descriptions j ON s.jd_id = j.id WHERE s.recruiter_id = %s ORDER BY s.id DESC"
        cursor.execute(query, (recruiter_id,))
        return cursor.fetchall()
    finally:
        db.close()