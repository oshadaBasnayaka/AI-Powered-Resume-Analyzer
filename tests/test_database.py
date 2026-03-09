import pytest
from unittest.mock import MagicMock, patch
from database_helper import save_analysis_to_db


@patch('database_helper.get_db_connection')
def test_save_analysis_to_db_success(mock_get_conn):
    # Setup: Create a mock database connection and cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_conn.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    # Mock the 'lastrowid' for JD and Resume inserts
    mock_cursor.lastrowid = 1

    # Execute the function
    result = save_analysis_to_db(
        user_id=1,
        resume_name="test.pdf",
        jd_text="Need Python",
        score=85.0,
        gaps=["Docker"]
    )

    # Verify: Did it return True? Did it call commit?
    assert result is True
    assert mock_conn.commit.called
    assert mock_cursor.execute.call_count == 3  # JD, Resume, and Analysis inserts