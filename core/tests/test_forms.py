import pytest

from core.forms import NounForm


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
