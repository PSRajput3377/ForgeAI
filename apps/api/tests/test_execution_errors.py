"""Tests for error classification."""

from execution.errors import ErrorCategory, classify_error


def test_classify_missing_python_module():
    err = classify_error("ModuleNotFoundError: No module named 'jwt'")
    assert err.category == ErrorCategory.DEPENDENCY
    assert "jwt" in err.hint
    assert err.retryable


def test_classify_missing_node_module():
    err = classify_error("Error: Cannot find module 'express'")
    assert err.category == ErrorCategory.DEPENDENCY
    assert "express" in err.hint


def test_classify_syntax_error():
    err = classify_error(
        "  File 'a.py', line 3\n    def f(\n        ^\nSyntaxError: invalid syntax"
    )
    assert err.category == ErrorCategory.SYNTAX


def test_classify_test_failure():
    err = classify_error("", "1 failed, 3 passed\nAssertionError: expected 200 got 500")
    assert err.category == ErrorCategory.TEST_FAILURE


def test_classify_security_secret_not_retryable():
    err = classify_error('API_KEY="sk-live-abc123"')
    assert err.category == ErrorCategory.SECURITY
    assert not err.retryable


def test_classify_timeout():
    err = classify_error("", timed_out=True)
    assert err.category == ErrorCategory.TIMEOUT


def test_classify_unknown():
    err = classify_error("some weird output with no known pattern xyz")
    assert err.category == ErrorCategory.UNKNOWN
