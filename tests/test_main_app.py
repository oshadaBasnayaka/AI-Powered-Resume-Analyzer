import pytest
from unittest.mock import patch, MagicMock
import main_app


# ---------------------------------------------------------
# 1. Test Utility Functions
# ---------------------------------------------------------
def test_hash_password():
    """Verify the SHA-256 hashing works correctly."""
    password = "secure_password"
    # The correct actual SHA-256 hash for the string "secure_password"
    expected_hash = "ff2f12ec5c6a2e9ef6b61c958ed701c327469190a18075fd909ec2a9b42b94f2"

    assert main_app.hash_password(password) == expected_hash


# ---------------------------------------------------------
# 2. Test Login Page
# ---------------------------------------------------------
@patch('main_app.st')
@patch('main_app.get_db_connection')
def test_login_page_success(mock_get_db, mock_st):
    """Simulate a user successfully logging in."""

    # 1. Setup an empty Streamlit session state
    mock_st.session_state = {}

    # ---------------------------------------------------------
    # NEW FIX: Teach the mock how to handle st.columns unpacking
    # ---------------------------------------------------------
    def mock_columns(spec):
        # If they passed an integer like st.columns(2)
        if isinstance(spec, int):
            return [MagicMock() for _ in range(spec)]
        # If they passed a list like st.columns([1, 2, 1])
        elif isinstance(spec, list):
            return [MagicMock() for _ in range(len(spec))]

    mock_st.columns.side_effect = mock_columns
    # ---------------------------------------------------------

    # 2. Mock the text inputs (Email, then Password)
    mock_st.text_input.side_effect = ["user@example.com", "password123"]

    # 3. Mock the buttons
    # Streamlit buttons return True when clicked. We want "Login" to be clicked.
    def mock_button(label, **kwargs):
        if label == "Login":
            return True
        return False

    mock_st.button.side_effect = mock_button

    # 4. Mock the Database to return a valid user record
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    mock_cursor.fetchone.return_value = {
        'id': 99,
        'full_name': 'Test Candidate',
        'user_role': 'Job Seeker'
    }

    # Execute the function
    main_app.login_page()

    # Verify the results: Did the session state update correctly?
    assert mock_st.session_state['logged_in'] is True
    assert mock_st.session_state['username'] == 'Test Candidate'
    assert mock_st.session_state['user_id'] == 99

    # Verify the app triggers a rerun after successful login
    mock_st.rerun.assert_called_once()


# ---------------------------------------------------------
# 3. Test Registration Page
# ---------------------------------------------------------
@patch('main_app.st')
@patch('main_app.get_db_connection')
def test_register_page_success(mock_get_db, mock_st):
    """Simulate a user creating a new account."""

    # 1. Setup session state
    mock_st.session_state = {'register_mode': True}

    # 2. Mock the inputs (Full Name, Email, Password)
    mock_st.text_input.side_effect = ["Jane Doe", "jane@example.com", "secure123"]

    # Mock the role dropdown
    mock_st.selectbox.return_value = "Recruiter"

    # 3. Mock the buttons ("Back" = False, "Create Account" = True)
    def mock_button(label, **kwargs):
        if label == "Create Account":
            return True
        return False

    mock_st.button.side_effect = mock_button

    # 4. Mock the Database insertion
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    # Execute the function
    main_app.register_page()

    # Verify the results
    # Check that the DB insert query was called
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()

    # Check that success message was shown and state was reset
    assert mock_st.success.called
    assert mock_st.session_state['register_mode'] is False
    mock_st.rerun.assert_called_once()