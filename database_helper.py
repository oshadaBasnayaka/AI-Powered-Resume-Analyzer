import mysql.connector


def get_db_connection():
    """
    Establish and return a MySQL database connection.
    Returns None if the connection fails.
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
    Save a single resume analysis result.
    Inserts the JD, Resume, and links them in the analysis_results table.
    """
    db = get_db_connection()
    if not db: return False

    try:
        cursor = db.cursor()

        # Insert the job description
        cursor.execute("INSERT INTO job_descriptions (job_title, jd_content, created_by) VALUES (%s, %s, %s)",
                       ("Analysis Target", jd_text, user_id))
        jd_id = cursor.lastrowid

        # Insert the resume metadata
        cursor.execute("INSERT INTO resumes (user_id, file_name) VALUES (%s, %s)", (user_id, resume_name))
        res_id = cursor.lastrowid

        # Convert gaps list to a comma-separated string if needed
        gaps_str = ", ".join(gaps) if isinstance(gaps, list) else gaps

        # Save the final score and link the JD and Resume IDs
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
    Get the 10 most recent resume analyses for a specific job seeker.
    """
    db = get_db_connection()
    if not db: return []

    try:
        cursor = db.cursor(dictionary=True)
        # Join analysis results with resumes to get filenames and scores
        query = """
            SELECT r.file_name, a.match_score, a.skill_gap_analysis 
            FROM analysis_results a 
            JOIN resumes r ON a.resume_id = r.id 
            WHERE a.user_id = %s 
            ORDER BY a.id DESC LIMIT 10
        """
        cursor.execute(query, (user_id,))
        return cursor.fetchall()
    finally:
        db.close()


# --- RECRUITER FUNCTIONS ---

def save_full_shortlist(recruiter_id, jd_text, title, candidates_list):
    """
    Save a batch of ranked candidates as a shortlist for recruiters.
    """
    db = get_db_connection()
    if not db: return False

    try:
        cursor = db.cursor()

        # Create the JD entry
        cursor.execute("INSERT INTO job_descriptions (job_title, jd_content, created_by) VALUES (%s, %s, %s)",
                       (title, jd_text, recruiter_id))
        jd_id = cursor.lastrowid

        # Create the shortlist header
        cursor.execute("INSERT INTO shortlists (recruiter_id, jd_id, title) VALUES (%s, %s, %s)",
                       (recruiter_id, jd_id, title))
        shortlist_id = cursor.lastrowid

        # Loop through the ranked candidates and save them
        for rank, cand in enumerate(candidates_list, start=1):
            # Insert candidate resume
            cursor.execute("INSERT INTO resumes (user_id, file_name) VALUES (%s, %s)",
                           (recruiter_id, cand['Candidate']))
            res_id = cursor.lastrowid

            # Save the match score for this candidate
            cursor.execute(
                "INSERT INTO analysis_results (resume_id, jd_id, user_id, match_score) VALUES (%s, %s, %s, %s)",
                (res_id, jd_id, recruiter_id, cand['Score']))
            analysis_id = cursor.lastrowid

            # Link the candidate to the shortlist with their specific rank
            cursor.execute(
                "INSERT INTO shortlist_items (shortlist_id, resume_id, analysis_result_id, rank_order) VALUES (%s, %s, %s, %s)",
                (shortlist_id, res_id, analysis_id, rank))

        db.commit()
        return True
    finally:
        db.close()


def fetch_recruiter_shortlists(recruiter_id):
    """
    Get all saved shortlists to display on the recruiter dashboard.
    """
    db = get_db_connection()
    if not db: return []

    try:
        cursor = db.cursor(dictionary=True)
        # Fetch shortlist details along with the targeted job title
        query = """
            SELECT s.id, s.title, j.job_title, s.created_at 
            FROM shortlists s 
            JOIN job_descriptions j ON s.jd_id = j.id 
            WHERE s.recruiter_id = %s 
            ORDER BY s.id DESC
        """
        cursor.execute(query, (recruiter_id,))
        return cursor.fetchall()
    finally:
        db.close()