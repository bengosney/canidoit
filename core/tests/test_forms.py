import pytest

from core.forms import NounForm
from core.models import MAX_NOUN_LENGTH


@pytest.mark.parametrize(("raw", "expected"), [("Cat", "cat"), ("  Hot Tub  ", "hot tub"), ("MOOSE", "moose")])
def test_noun_is_normalised(raw, expected):
    form = NounForm({"noun": raw})

    assert form.is_valid()
    assert form.cleaned_data["noun"] == expected


@pytest.mark.parametrize("raw", ["", "   "])
def test_blank_noun_is_rejected(raw):
    assert not NounForm({"noun": raw}).is_valid()


def test_unbound_form_has_no_errors():
    assert NounForm().errors == {}


@pytest.mark.parametrize("noun", ["fuck", "a stupid cunt", "shit", "wanker"])
def test_profane_nouns_are_rejected(noun):
    form = NounForm({"noun": noun})

    assert not form.is_valid()
    assert form.errors["noun"] == ["Keep it clean."]


@pytest.mark.parametrize("noun", ["kettle", "my boss", "the moon", "a goose"])
def test_ordinary_nouns_are_accepted(noun):
    assert NounForm({"noun": noun}).is_valid()


def test_the_threshold_is_what_decides(mocker):
    mocker.patch("core.forms.profanity.is_profane", return_value=True)

    assert not NounForm({"noun": "kettle"}).is_valid()


@pytest.mark.parametrize("noun", ["shitbag", "arsegoblin"])
def test_compound_words_slip_through(noun):
    """Documents a known gap: the classifier is bag-of-words, so novel
    compounds score low. Change this test if the filter is ever tightened."""
    assert NounForm({"noun": noun}).is_valid()


def test_a_noun_at_the_limit_is_accepted():
    assert NounForm({"noun": "a" * MAX_NOUN_LENGTH}).is_valid()


def test_a_noun_over_the_limit_is_rejected():
    form = NounForm({"noun": "a" * (MAX_NOUN_LENGTH + 1)})

    assert not form.is_valid()
    assert "noun" in form.errors


def test_the_form_limit_follows_the_model():
    """They must not drift: the column would reject what the form allowed."""
    assert NounForm().fields["noun"].max_length == MAX_NOUN_LENGTH


def test_the_input_advertises_the_limit():
    assert f'maxlength="{MAX_NOUN_LENGTH}"' in str(NounForm()["noun"])
