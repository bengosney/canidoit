"""The only code that talks to the self-hosted model.

Every answer is a refusal, and the model is never told what was asked about.
It writes a general-purpose "no" and nothing else, so it cannot endorse
anything, and cannot say something regrettable about a real person or a
specific thing.

`generate` never raises: a model that is slow, down, or talking nonsense is an
ordinary outcome here, and the caller just leaves the noun for another attempt.
"""

import json
import logging
import re

from django.conf import settings

import requests

from core import profanity

logger = logging.getLogger(__name__)

# Grammar-constrained, so even a 0.5B model stays in format.
SCHEMA = {
    "type": "object",
    "properties": {"response": {"type": "string"}},
    "required": ["response"],
}

# Small models drift into answering as though asked about their own abilities
# ("Of course, I'd love to", "I can't assist with that"). The prompt discourages
# it; this catches the rest.
FIRST_PERSON = re.compile(r"\b(i|i'm|i'll|i'd|me|my|mine|myself|we|us|our)\b", re.IGNORECASE)

# Deliberately says nothing about what was asked: the noun is not interpolated,
# so the model has no opportunity to comment on it. Every example starts with a
# refusal word, because the failure mode is sliding into assistant voice ("I
# cannot agree", "I'm not sure") rather than refusing in character.
PROMPT = (
    "Someone has asked permission to do something. The answer is no.\n"
    "Write ONE short, funny, general-purpose refusal, under 15 words.\n"
    "Start with a word like No, Never, Absolutely, Out, Certainly, Put, Step, Walk or You.\n"
    "Never start with 'I'. Never write the words I, me or my. "
    "Never mention yourself or your opinions.\n"
    "Keep it clean: no swearing, no crude words, nothing explicit. "
    "Do not guess what they asked about.\n\n"
    '{"response": "Absolutely not. Have a long think about your choices."}\n'
    '{"response": "No. Put it down and walk away slowly."}\n'
    '{"response": "Out of the question, and you know exactly why."}\n'
    '{"response": "No, and frankly you should not have asked."}\n'
    '{"response": "Never. Step away and pretend this never happened."}\n'
    '{"response": "Certainly not. You knew the answer before you asked."}\n'
)

# Below ~60 the JSON gets truncated mid-string and won't parse.
MAX_TOKENS = 60

# Nothing longer than this gets stored, whatever the model does.
MAX_RESPONSE_LENGTH = 300


def _ask() -> str:
    """One round trip to the model. Raises on any transport-level problem."""
    reply = requests.post(
        f"{settings.LLM_BASE_URL}/api/generate",
        json={
            "model": settings.LLM_MODEL,
            "prompt": PROMPT,
            "format": SCHEMA,
            "stream": False,
            "keep_alive": 0,
            "options": {"num_predict": MAX_TOKENS, "temperature": 0.9},
        },
        timeout=settings.LLM_TIMEOUT,
    )
    reply.raise_for_status()
    return reply.json()["response"]


def _usable(raw: str) -> str | None:
    """Parse and vet one reply, or None with the reason logged."""
    try:
        response = json.loads(raw)["response"].strip()
    except json.JSONDecodeError, KeyError, TypeError, AttributeError:
        logger.warning("Model returned unparseable output: %r", raw[-40:])
        return None

    if not response:
        logger.warning("Model returned an empty response")
        return None

    if FIRST_PERSON.search(response):
        logger.warning("Model answered about itself: %r", response[:60])
        return None

    if profanity.is_profane(response):
        logger.warning("Model was not clean: %r", response[:60])
        return None

    return response[:MAX_RESPONSE_LENGTH]


def generate() -> str | None:
    """One refusal for the pool, or None if the model produced nothing usable.

    One call per invocation. A fumbled reply costs nothing beyond a pool slot
    staying empty a little longer, so there is no retry here.
    """
    if not settings.LLM_ENABLED:
        return None

    try:
        raw = _ask()
    except requests.RequestException, KeyError, TypeError:
        logger.warning("Could not reach the model", exc_info=True)
        return None

    return _usable(raw)
