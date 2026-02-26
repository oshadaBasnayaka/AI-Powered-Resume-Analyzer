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