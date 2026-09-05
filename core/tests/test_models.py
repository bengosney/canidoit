from django.db.models import ProtectedError
from django.db.utils import IntegrityError

import pytest

from core.models import Response, Subject


def make(noun, text="No."):
    return Subject.objects.create(noun=noun, response=Response.objects.create(text=text))


@pytest.mark.django_db
def test_noun_is_normalised():
    subject = make("  Cat  ")

    assert subject.noun == "cat"
    assert Subject.objects.get(noun="cat") == subject


@pytest.mark.django_db
def test_noun_is_unique():
    make("cat", "First.")

    with pytest.raises(IntegrityError):
        make("cat", "Second.")


@pytest.mark.django_db
def test_str_is_the_noun():
    assert str(make("cat")) == "cat"


@pytest.mark.django_db
def test_ordering_is_by_noun():
    for noun in ["zebra", "aardvark", "moose"]:
        make(noun, f"No to {noun}.")

    assert [s.noun for s in Subject.objects.all()] == ["aardvark", "moose", "zebra"]


@pytest.mark.django_db
def test_response_text_is_unique():
    Response.objects.create(text="Absolutely not.")

    with pytest.raises(IntegrityError):
        Response.objects.create(text="Absolutely not.")


@pytest.mark.django_db
def test_a_response_can_only_be_claimed_once():
    response = Response.objects.create(text="Absolutely not.")
    Subject.objects.create(noun="cat", response=response)

    with pytest.raises(IntegrityError):
        Subject.objects.create(noun="moose", response=response)


@pytest.mark.django_db
def test_a_claimed_response_cannot_be_deleted():
    subject = make("cat")

    with pytest.raises(ProtectedError):
        subject.response.delete()


@pytest.mark.django_db
def test_str_of_a_response_is_its_text():
    assert str(Response.objects.create(text="Absolutely not.")) == "Absolutely not."
