"""
tests/test_trashgpt.py

Tests for POST /api/chat (TrashGPT)

Provider: OpenAI (gpt-4o-mini by default)
Model: configurable via LLM_MODEL env var
Trained by: OpenAI. NOT trained by Wrapture.
TrashGPT is an LLM-powered sustainability assistant that uses a pretrained
general-purpose language model.

All tests that would require a real paid API call mock the OpenAI client
at the HTTP boundary using unittest.mock. The production code path is
unchanged — only the external HTTP call is intercepted.

Run from backend/:
    python -m pytest tests/test_trashgpt.py -v

Test cases:
1.  Valid message with configured provider → OK + real response structure
2.  Empty message → 400
3.  Missing message field → 400
4.  Missing API key → NOT_CONFIGURED (no fake answer)
5.  Provider authentication error → AUTH_ERROR, safe message
6.  Provider timeout → TIMEOUT, safe message
7.  Provider rate limit → RATE_LIMIT, safe message
8.  Successful response structure — all required fields present
9.  API key never appears in response
10. No canned/random fallback — response comes from mocked LLM, not hardcoded
"""
import sys
import os
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import openai
from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as c:
        yield c


# ── Mock helpers ──────────────────────────────────────────────────────────────

def _mock_completion(content: str):
    """Build a minimal mock that looks like an OpenAI ChatCompletion response."""
    choice = MagicMock()
    choice.message.content = content
    completion = MagicMock()
    completion.choices = [choice]
    return completion


def _patch_openai(content: str):
    """Context manager: patch OpenAI.chat.completions.create to return content."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_completion(content)
    return patch('services.chatbot.OpenAI', return_value=mock_client)


def _patch_openai_error(exc_instance):
    """Context manager: patch OpenAI client to raise exc_instance."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = exc_instance
    return patch('services.chatbot.OpenAI', return_value=mock_client)


# ── 1. Valid message with configured provider ─────────────────────────────────

def test_valid_message_configured(client):
    fake_response = 'Corrugated cardboard is widely recyclable in most curbside programs.'
    with _patch_openai(fake_response):
        with patch('config.LLM_API_KEY', 'sk-test-key'):
            r = client.post('/api/chat', json={'message': 'What packaging is recyclable?'})

    assert r.status_code == 200
    data = r.get_json()
    assert data['status'] == 'OK'
    assert data['response'] == fake_response
    assert data['model'] is not None
    assert data['provider'] == 'openai'


# ── 2. Empty message → 400 ────────────────────────────────────────────────────

def test_empty_message(client):
    r = client.post('/api/chat', json={'message': ''})
    assert r.status_code == 400
    data = r.get_json()
    assert 'error' in data


# ── 3. Missing message field → 400 ───────────────────────────────────────────

def test_missing_message_field(client):
    r = client.post('/api/chat', json={})
    assert r.status_code == 400
    data = r.get_json()
    assert 'error' in data


# ── 4. Missing API key → NOT_CONFIGURED ──────────────────────────────────────

def test_missing_api_key_not_configured(client):
    with patch('config.LLM_API_KEY', ''):
        r = client.post('/api/chat', json={'message': 'What is recyclable?'})

    assert r.status_code == 200
    data = r.get_json()
    assert data['status'] == 'NOT_CONFIGURED'
    assert data['response'] is None
    # Must explain the situation — not a fake answer
    assert 'LLM_API_KEY' in data['error'] or 'not configured' in data['error'].lower()


# ── 5. Provider authentication error ─────────────────────────────────────────

def test_auth_error(client):
    exc = openai.AuthenticationError(
        message='Incorrect API key',
        response=MagicMock(status_code=401, headers={}),
        body={'error': {'message': 'Incorrect API key', 'type': 'invalid_request_error'}},
    )
    with _patch_openai_error(exc):
        with patch('config.LLM_API_KEY', 'sk-bad-key'):
            r = client.post('/api/chat', json={'message': 'Hello'})

    assert r.status_code == 200
    data = r.get_json()
    assert data['status'] == 'AUTH_ERROR'
    assert data['response'] is None
    # Safe message — must not expose the key
    assert 'sk-bad-key' not in data.get('error', '')
    assert 'sk-bad-key' not in json.dumps(data)


# ── 6. Provider timeout ───────────────────────────────────────────────────────

def test_provider_timeout(client):
    exc = openai.APITimeoutError(request=MagicMock())
    with _patch_openai_error(exc):
        with patch('config.LLM_API_KEY', 'sk-test-key'):
            r = client.post('/api/chat', json={'message': 'Hello'})

    assert r.status_code == 200
    data = r.get_json()
    assert data['status'] == 'TIMEOUT'
    assert data['response'] is None
    assert 'timed out' in data['error'].lower() or 'timeout' in data['error'].lower()


# ── 7. Provider rate limit ────────────────────────────────────────────────────

def test_provider_rate_limit(client):
    exc = openai.RateLimitError(
        message='Rate limit exceeded',
        response=MagicMock(status_code=429, headers={}),
        body={'error': {'message': 'Rate limit exceeded', 'type': 'rate_limit_error'}},
    )
    with _patch_openai_error(exc):
        with patch('config.LLM_API_KEY', 'sk-test-key'):
            r = client.post('/api/chat', json={'message': 'Hello'})

    assert r.status_code == 200
    data = r.get_json()
    assert data['status'] == 'RATE_LIMIT'
    assert data['response'] is None
    assert 'rate limit' in data['error'].lower()


# ── 8. Successful response structure ─────────────────────────────────────────

def test_successful_response_structure(client):
    fake_response = 'Use corrugated cardboard for fragile items — it is recyclable and protective.'
    with _patch_openai(fake_response):
        with patch('config.LLM_API_KEY', 'sk-test-key'):
            r = client.post('/api/chat', json={
                'message': 'Best packaging for fragile items?',
                'history': [
                    {'role': 'user',      'content': 'Hi'},
                    {'role': 'assistant', 'content': 'Hello! How can I help?'},
                ],
            })

    assert r.status_code == 200
    data = r.get_json()
    # All required fields must be present
    assert 'status'   in data
    assert 'response' in data
    assert 'model'    in data
    assert 'provider' in data
    assert data['status']   == 'OK'
    assert data['response'] == fake_response
    assert data['provider'] == 'openai'
    assert data['model']    is not None


# ── 9. API key never appears in response ─────────────────────────────────────

def test_api_key_never_in_response(client):
    sentinel_key = 'sk-sentinel-key-must-not-appear-in-response'

    # Test OK path
    with _patch_openai('Some response text.'):
        with patch('config.LLM_API_KEY', sentinel_key):
            r = client.post('/api/chat', json={'message': 'Hello'})
    assert sentinel_key not in json.dumps(r.get_json())

    # Test error path
    exc = openai.AuthenticationError(
        message='Bad key',
        response=MagicMock(status_code=401, headers={}),
        body={'error': {'message': 'Bad key', 'type': 'invalid_request_error'}},
    )
    with _patch_openai_error(exc):
        with patch('config.LLM_API_KEY', sentinel_key):
            r = client.post('/api/chat', json={'message': 'Hello'})
    assert sentinel_key not in json.dumps(r.get_json())


# ── 10. No canned/random fallback ────────────────────────────────────────────

def test_no_canned_fallback(client):
    """
    The response must come from the mocked LLM call, not from hardcoded strings.
    We use a unique sentinel string as the mock response and verify it is returned
    verbatim — proving the code path goes through the LLM call, not a fallback.
    """
    sentinel = 'UNIQUE_SENTINEL_RESPONSE_XYZ_12345_NOT_HARDCODED'
    with _patch_openai(sentinel):
        with patch('config.LLM_API_KEY', 'sk-test-key'):
            r = client.post('/api/chat', json={'message': 'Tell me about packaging.'})

    assert r.status_code == 200
    data = r.get_json()
    assert data['status'] == 'OK'
    # The exact sentinel must be returned — proves no canned response was substituted
    assert data['response'] == sentinel
