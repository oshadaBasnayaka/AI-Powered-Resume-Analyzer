import pytest
from processor import calculate_match_score, find_missing_skills


def test_calculate_match_score():


    resume = "Python developer with experience in SQL and AWS."
    jd = "Looking for a Python developer who knows SQL."

    score = calculate_match_score(resume, jd)

    assert isinstance(score, float)
    assert score > 0
    assert score <= 100


def test_find_missing_skills():
    resume = "I know Python and Java"
    jd = "Requirements: Python, Java, Docker, Kubernetes"

    gaps = find_missing_skills(resume, jd)

    # Check that 'docker' and 'kubernetes' are identified
    assert "docker" in gaps
    assert "kubernetes" in gaps
    # Check that 'python' is NOT in gaps
    assert "python" not in gaps