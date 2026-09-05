from django.db.utils import IntegrityError

import pytest

from core.models import Subject


@pytest.mark.django_db
def test_slug_is_generated_from_noun():
    subject = Subject.objects.create(noun="Hot Tub", verdict=Subject.Verdict.MAYBE, response="Only if it's clean.")
    assert subject.slug == "hot-tub"


@pytest.mark.django_db
def test_noun_is_normalised():
    subject = Subject.objects.create(noun="  Cat  ", verdict=Subject.Verdict.NO, response="No.")
    assert subject.noun == "cat"
    assert Subject.objects.get(noun="cat") == subject


@pytest.mark.django_db
def test_explicit_slug_is_kept():
    subject = Subject.objects.create(noun="bicycle", slug="bike", verdict=Subject.Verdict.YES, response="Yes.")
    assert subject.slug == "bike"


@pytest.mark.django_db
def test_noun_is_unique():
    Subject.objects.create(noun="cat", verdict=Subject.Verdict.NO, response="No.")
    with pytest.raises(IntegrityError):
        Subject.objects.create(noun="cat", verdict=Subject.Verdict.YES, response="Yes.")


@pytest.mark.django_db
def test_str_is_the_noun():
    assert str(Subject.objects.create(noun="cat", verdict=Subject.Verdict.NO, response="No.")) == "cat"


@pytest.mark.django_db
def test_ordering_is_by_noun():
    for noun in ["zebra", "aardvark", "moose"]:
        Subject.objects.create(noun=noun, verdict=Subject.Verdict.YES, response="Yes.")
    assert [s.noun for s in Subject.objects.all()] == ["aardvark", "moose", "zebra"]
