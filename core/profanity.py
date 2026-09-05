"""Scoring text for profanity, used on both what visitors type and what the
model writes.

`alt-profanity-check` is a small linear model over scikit-learn. Importing it
costs around 116MB of RSS, paid once per process at startup.
"""

from profanity_check import predict_prob

THRESHOLD = 0.5


def score(text: str) -> float:
    """How likely the text is to be offensive, between 0 and 1."""
    return float(predict_prob([text])[0])


def is_profane(text: str) -> bool:
    return score(text) >= THRESHOLD
