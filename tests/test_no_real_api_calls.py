"""CRITICAL TEST: Verify that NO real API calls are made during testing.

This test ensures that the mocking infrastructure is working correctly
and that running the test suite will NOT consume OpenAI API quota.
"""

import pytest
from unittest.mock import MagicMock
import llm
import requests


def test_requests_post_is_mocked():
    """CRITICAL: Verify that requests.post is mocked and will not make real API calls."""
    # Both llm.requests.post and requests.post should be MagicMock instances
    assert isinstance(llm.requests.post, MagicMock), \
        f"CRITICAL FAILURE: llm.requests.post is NOT mocked! Type: {type(llm.requests.post)}. " \
        f"Real API calls WILL be made!"
    
    assert isinstance(requests.post, MagicMock), \
        f"CRITICAL FAILURE: requests.post is NOT mocked! Type: {type(requests.post)}. " \
        f"Real API calls WILL be made!"


def test_mock_returns_test_response():
    """Verify that the mock returns the expected test response."""
    # Call the mocked function
    response = llm.requests.post("https://api.openai.com/v1/chat/completions", json={})
    
    # Should return a MagicMock with json() method
    assert hasattr(response, 'json')
    
    # Call json() to get the response data
    data = response.json()
    
    # Should return our test response structure
    assert "choices" in data
    assert "usage" in data
    assert data["choices"][0]["message"]["content"] == "Test response"
    
    # Verify this was a mock call, not a real HTTP request
    assert llm.requests.post.called


def test_no_real_http_requests():
    """Verify that making a 'request' does not result in a real HTTP call."""
    # This should NOT make a real HTTP request
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": "Bearer fake-key"},
        json={"model": "gpt-5.1", "messages": []}
    )
    
    # Should get mock response, not a real HTTP response
    assert isinstance(response, MagicMock)
    assert hasattr(response, 'json')
    
    # Verify the mock was called (proving it intercepted the call)
    assert requests.post.called
    
    # The URL and data should have been passed to the mock
    call_args = requests.post.call_args
    assert call_args is not None

