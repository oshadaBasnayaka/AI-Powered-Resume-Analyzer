import pytest
from unittest.mock import MagicMock, patch
from processor import extract_text_from_pdf


@patch('fitz.open')
def test_extract_text_from_pdf(mock_fitz_open):
    # Mock the PDF document structure
    mock_doc = MagicMock()
    mock_page = MagicMock()
    mock_page.get_text.return_value = "This is resume text."
    mock_doc.__iter__.return_value = [mock_page]
    mock_fitz_open.return_value = mock_doc

    # Create a dummy file-like object
    fake_file = MagicMock()

    text = extract_text_from_pdf(fake_file)

    assert text == "This is resume text."
    mock_doc.close.assert_called_once()