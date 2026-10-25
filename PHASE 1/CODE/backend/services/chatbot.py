"""
services/chatbot.py

Routes chat messages to a real LLM provider.
If LLM_API_KEY is not set, returns a clear NOT_CONFIGURED response.

Does NOT:
- fall back to canned keyword responses
- pretend to be AI when it is not
- expose API keys or internal stack traces
- fabricate responses

Supported providers:
  openai — uses openai Python SDK (gpt-4o-mini by default)

Environment variables (set in backend/.env):
  LLM_PROVIDER   openai | none   (default: openai)
  LLM_API_KEY    your OpenAI API key
  LLM_MODEL      model name      (default: gpt-4o-mini)
"""
import config
from openai import OpenAI
import openai as _openai_module

# ── System prompt ─────────────────────────────────────────────────────────────
# Defines TrashGPT's role, scope, and honesty constraints.
# Does NOT claim Wrapture-specific training.

SYSTEM_PROMPT = """\
You are TrashGPT, an LLM-powered sustainability assistant for the Wrapture platform.

Wrapture is a packaging recommendation tool that:
- Matches product dimensions to real packaging from the Packrift catalog (2,209 records)
- Classifies packaging materials: corrugated_cardboard, kraft_paper, plastic, unknown
- Analyzes customer review sentiment using DistilBERT SST-2
- Provides CO2 recycling data (co2e_recycling_mt) and per-unit pricing from the catalog

You help users with:
- Packaging material selection and sustainability trade-offs
- Recycling guidance and waste disposal best practices
- Eco-friendly packaging alternatives
- Understanding packaging environmental impact concepts
- Interpreting Wrapture packaging recommendations and catalog metrics
- CO2 and lifecycle concepts in packaging (general knowledge only)
- Packaging waste reduction strategies

Honesty constraints — you MUST follow these:
- Do not invent specific CO2 values, prices, or product dimensions
- Do not fabricate recycling statistics or scientific claims
- Do not claim to have access to the user's specific catalog results unless they paste them
- If the user needs exact Wrapture data (dimensions, prices, CO2), tell them to use the
  Packaging Recommender, Packaging Simulator, or Vision Scanner modules
- If you do not know something, say so clearly
- You are a pretrained general LLM used by Wrapture — you were not trained by Wrapture

Keep responses concise and practical. Use plain language.\
"""

# ── Error message sanitiser ───────────────────────────────────────────────────
# Never expose raw exception strings to the frontend.

def _safe_error(exc) -> tuple[str, str]:
    """
    Classify an OpenAI exception into a user-safe status and message.
    Returns (status, message).
    """
    if isinstance(exc, _openai_module.AuthenticationError):
        return 'AUTH_ERROR', 'The OpenAI API key is invalid or has been revoked.'
    if isinstance(exc, _openai_module.RateLimitError):
        return 'RATE_LIMIT', 'OpenAI rate limit reached. Please wait a moment and try again.'
    if isinstance(exc, _openai_module.APITimeoutError):
        return 'TIMEOUT', 'The request to OpenAI timed out. Please try again.'
    if isinstance(exc, _openai_module.APIConnectionError):
        return 'CONNECTION_ERROR', 'Could not connect to OpenAI. Check your network connection.'
    if isinstance(exc, _openai_module.APIStatusError):
        return 'PROVIDER_ERROR', f'OpenAI returned an error (HTTP {exc.status_code}).'
    return 'ERROR', 'An unexpected error occurred while contacting the AI provider.'


# ── Public interface ──────────────────────────────────────────────────────────

def chat(message: str, history: list = None) -> dict:
    """
    Send a message to the configured LLM.
    Returns the response or a clear structured error.
    Never exposes the API key or internal stack traces.
    """
    if not config.LLM_API_KEY:
        return {
            'status': 'NOT_CONFIGURED',
            'error': (
                'TrashGPT is not configured because no LLM API key is available. '
                'Set LLM_API_KEY in backend/.env to enable AI chat.'
            ),
            'response': None,
            'provider': config.LLM_PROVIDER,
            'model': None,
        }

    if config.LLM_PROVIDER == 'openai':
        return _call_openai(message, history or [])

    return {
        'status': 'UNSUPPORTED_PROVIDER',
        'error': f"LLM provider '{config.LLM_PROVIDER}' is not supported. Set LLM_PROVIDER=openai.",
        'response': None,
        'provider': config.LLM_PROVIDER,
        'model': None,
    }


def _call_openai(message: str, history: list) -> dict:
    try:
        client = OpenAI(api_key=config.LLM_API_KEY)

        # Build message list: system prompt + last 10 history turns + current message
        messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
        for turn in history[-10:]:
            role = turn.get('role', '')
            content = turn.get('content', '')
            if role in ('user', 'assistant') and content:
                messages.append({'role': role, 'content': content})
        messages.append({'role': 'user', 'content': message})

        completion = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=messages,
            max_tokens=600,
            temperature=0.7,
        )

        return {
            'status': 'OK',
            'response': completion.choices[0].message.content,
            'model': config.LLM_MODEL,
            'provider': 'openai',
        }

    except Exception as exc:
        status, msg = _safe_error(exc)
        return {
            'status': status,
            'error': msg,
            'response': None,
            'provider': 'openai',
            'model': config.LLM_MODEL,
        }
