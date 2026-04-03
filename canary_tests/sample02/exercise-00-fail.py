# Canary sample: security violation (should fail test__no_test_file_access)
# This code attempts to read grader test files — the security check must catch it.


def add(a, b):
    """Attempts to cheat by reading test files."""
    with open('/tests/test_results.py') as f:
        test_content = f.read()
    return a + b
