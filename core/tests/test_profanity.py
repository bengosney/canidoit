import pytest

from core import profanity

CLEAN = ["kettle", "the moon", "a goose", "Absolutely not. Have a long think about your choices."]
PROFANE = ["fuck", "a stupid cunt", "wanker", "No fucking way."]


@pytest.mark.parametrize("text", CLEAN)
def test_clean_text_scores_below_the_threshold(text):
    assert profanity.score(text) < profanity.THRESHOLD
    assert not profanity.is_profane(text)


@pytest.mark.parametrize("text", PROFANE)
def test_profane_text_scores_above_the_threshold(text):
    assert profanity.score(text) >= profanity.THRESHOLD
    assert profanity.is_profane(text)


def test_score_is_a_probability():
    assert 0.0 <= profanity.score("kettle") <= 1.0
