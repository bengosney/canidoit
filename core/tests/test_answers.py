import pytest

from core.answers import FALLBACKS, Answer, answer_for, save_random_subject
from core.models import Subject


@pytest.mark.django_db
def test_known_noun_returns_stored_answer():
    Subject.objects.create(noun="cat", verdict=Subject.Verdict.NO, response="Obviously not.")

    answer = answer_for("cat")

    assert answer == Answer(noun="cat", verdict="no", response="Obviously not.")


@pytest.mark.django_db
def test_lookup_normalises_the_noun():
    Subject.objects.create(noun="hot tub", verdict=Subject.Verdict.MAYBE, response="If it's clean.")

    assert answer_for("  Hot Tub  ").response == "If it's clean."
    assert Subject.objects.count() == 1


@pytest.mark.django_db
def test_unknown_noun_gets_an_invented_answer():
    answer = answer_for("aardvark")

    assert answer.noun == "aardvark"
    assert "aardvark" in answer.response


@pytest.mark.django_db
def test_unknown_noun_is_saved():
    answer_for("aardvark")

    assert Subject.objects.get(noun="aardvark").slug == "aardvark"


@pytest.mark.django_db
def test_invented_answer_is_stable_across_lookups():
    first = answer_for("aardvark")
    second = answer_for("aardvark")

    assert first == second
    assert Subject.objects.filter(noun="aardvark").count() == 1


@pytest.mark.django_db
def test_save_random_subject_uses_a_fallback(mocker):
    mocker.patch("core.answers.random.choice", return_value=(Subject.Verdict.YES, "Yes, {noun} is fine."))

    subject = save_random_subject("moose")

    assert (subject.verdict, subject.response) == ("yes", "Yes, moose is fine.")


@pytest.mark.django_db
def test_save_random_subject_is_idempotent():
    first = save_random_subject("moose")
    second = save_random_subject("moose")

    assert first.pk == second.pk


@pytest.mark.parametrize(("verdict", "template"), FALLBACKS)
def test_every_fallback_is_valid(verdict, template):
    assert verdict in Subject.Verdict.values
    assert "{noun}" in template


def test_verdict_display():
    assert Answer(noun="cat", verdict="maybe", response="").get_verdict_display == "Maybe"
