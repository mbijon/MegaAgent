"""Pytest configuration and shared fixtures."""

import os
import pytest
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import chromadb

# Global patch objects that will be started/stopped at session level
_requests_patches = []


# CRITICAL: Patch requests.post BEFORE any modules import it
# This must happen at module import time, not in a fixture
def _setup_requests_mock():
    """Set up the requests.post mock before any imports."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "Test response",
                    "role": "assistant",
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }

    # Patch BEFORE importing llm
    patch1 = patch("requests.post", return_value=mock_response)
    patch2 = patch("llm.requests.post", return_value=mock_response)

    mock_post = patch1.start()
    patch2.start()

    _requests_patches.extend([patch1, patch2])
    return mock_post


# Start the mock immediately when conftest is imported
_session_mock = None
try:
    _session_mock = _setup_requests_mock()
except:
    # If llm isn't imported yet, we'll set it up in the fixture
    pass


@pytest.fixture(autouse=True)
def cleanup_chromadb():
    """Clean up ChromaDB collections before each test."""
    yield
    # Clean up after test
    try:
        client = chromadb.Client()
        collections = client.list_collections()
        for collection in collections:
            try:
                client.delete_collection(collection.name)
            except:
                pass
    except:
        pass


@pytest.fixture
def temp_files_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_openai_api_key(monkeypatch):
    """Mock OpenAI API key for testing."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-api-key-12345")
    yield "test-api-key-12345"


@pytest.fixture
def mock_openai_model(monkeypatch):
    """Mock OpenAI model for testing."""
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.1")
    yield "gpt-5.1"


@pytest.fixture
def mock_enable_web_search(monkeypatch):
    """Mock web search enablement."""
    monkeypatch.setenv("ENABLE_WEB_SEARCH", "true")
    yield True


@pytest.fixture(scope="session", autouse=True)
def mock_requests_post_session():
    """Mock requests.post for the entire test session.

    This ensures ALL requests.post calls are intercepted, including those
    in threads that outlive individual test functions. The patch stays
    active for the entire test session.

    CRITICAL: This fixture MUST prevent any real API calls to OpenAI.
    """
    from unittest.mock import MagicMock

    global _session_mock

    # Use the pre-setup mock if available, otherwise create one
    if _session_mock is None:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Test response",
                        "role": "assistant",
                    }
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

        # CRITICAL: Patch at multiple levels to ensure NO real API calls
        patch1 = patch("llm.requests.post", return_value=mock_response)
        patch2 = patch("requests.post", return_value=mock_response)

        mock_llm_post = patch1.start()
        patch2.start()

        _requests_patches.extend([patch1, patch2])
        _session_mock = mock_llm_post

    # Verify patches are active - CRITICAL CHECK
    import llm
    import requests

    # Both should be mocked - if not, force patch
    if not isinstance(llm.requests.post, MagicMock):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test", "role": "assistant"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }
        p1 = patch("llm.requests.post", return_value=mock_response)
        p2 = patch("requests.post", return_value=mock_response)
        _session_mock = p1.start()
        p2.start()
        _requests_patches.extend([p1, p2])

    # Final verification - this will fail the test suite if mocking fails
    assert isinstance(llm.requests.post, MagicMock), (
        f"CRITICAL FAILURE: requests.post is NOT mocked! Type: {type(llm.requests.post)}. "
        f"Real API calls WILL be made and will consume your API quota!"
    )

    yield _session_mock

    # Keep patches active for entire session - don't stop them


@pytest.fixture(autouse=True)
def mock_requests_post(mock_requests_post_session):
    """Per-test fixture that provides access to the session-level mock.

    This fixture resets the mock state before each test so tests can
    customize the mock behavior (side_effect, return_value, etc.)

    CRITICAL: llm.py calls 'requests.post' directly. Since llm does
    'import requests', llm.requests IS the requests module, so
    llm.requests.post and requests.post are the same object.
    """
    import llm
    import requests

    # Reset the mock before each test
    mock_requests_post_session.reset_mock()

    # CRITICAL: Ensure requests.post (which llm.py uses) is the same mock
    # Since llm.requests is the requests module, they should already be the same
    # But we verify and ensure alignment
    assert isinstance(
        requests.post, MagicMock
    ), f"requests.post is not mocked! This will cause real API calls!"

    # Yield the mock - when tests modify mock_requests_post, it affects requests.post
    # because they're the same object (patched to the same mock)
    yield mock_requests_post_session

    # Reset after test to prevent side effects
    mock_requests_post_session.reset_mock()


@pytest.fixture(autouse=True)
def reset_llm_counters():
    """Reset LLM token counters before each test."""
    import llm

    llm.input_token = 0
    llm.output_token = 0
    yield
    llm.input_token = 0
    llm.output_token = 0
