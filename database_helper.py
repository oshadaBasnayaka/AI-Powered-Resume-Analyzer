import mysql.connector


# This function establishes a secure connection between Python and the MySQL database.
# It uses the host, user, password, and the specific database name we created.
def get_db_connection():
    try:
        # Initializing the connection with database credentials
        connection = mysql.connector.connect(
            host="localhost",  # The server address (usually localhost for development)
            user="root",  # Default MySQL username
            password="12345",  # My password
            database="resume_analyzer_db"  # Name of the database we created in MySQL Workbench
        )
        return connection

    except mysql.connector.Error as err:
        # If there is an error (e.g., wrong password), it will be printed here
        print(f"Database Connection Error: {err}")
        return None


# The following block is used for testing the connection.
# It only runs when you execute this specific file.
if __name__ == "__main__":
    conn = get_db_connection()
    if conn:
        print("Successfully connected to the database!")
        # Closing the connection after testing
        conn.close()
    else:
        print("Failed to connect. Please check your MySQL service and credentials.")


def save_analysis_result(user_id, resume_name, jd_text, match_score, missing_skills):
    db = get_db_connection()
    if db:
        try:
            cursor = db.cursor()

            query = """
                INSERT INTO analysis_results (user_id, resume_name, job_description, match_score, missing_skills) 
                VALUES (%s, %s, %s, %s, %s)
            """

            skills_str = ", ".join(missing_skills) if isinstance(missing_skills, list) else missing_skills

            values = (user_id, resume_name, jd_text, match_score, skills_str)

            cursor.execute(query, values)
            db.commit()
            cursor.close()
            db.close()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False
    return False

def get_user_analysis_history(user_id):
    """
    Fetches the last 10 analysis results for a specific user.
    English: We use an ORDER BY clause to show the most recent analysis first.
    """
    db = get_db_connection()
    if db:
        try:
            cursor = db.cursor(dictionary=True)
            # Fetching results ordered by latest first
            query = "SELECT resume_name, match_score, missing_skills FROM analysis_results WHERE user_id = %s ORDER BY id DESC LIMIT 10"
            cursor.execute(query, (user_id,))
            results = cursor.fetchall()
            cursor.close()
            db.close()
            return results
        except Exception as e:
            print(f"Error fetching history: {e}")
            return []
    return []