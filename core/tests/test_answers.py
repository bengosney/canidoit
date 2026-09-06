import pytest

from core.answers import FALLBACKS, answer_for, case_number, claim_response, save_random_subject
from core.models import Response, Subject


def make(noun, text):
    return Subject.objects.create(noun=noun, response=Response.objects.create(text=text))


@pytest.mark.django_db
def test_known_noun_returns_its_stored_answer():
    subject = make("cat", "Obviously not.")

    answer = answer_for("cat")

    assert (answer.noun, answer.response) == ("cat", "Obviously not.")
    assert answer.case_no == case_number(subject.pk)
    assert answer.issued == subject.response.created


@pytest.mark.django_db
def test_lookup_normalises_the_noun():
    make("hot tub", "If it's clean.")

    assert answer_for("  Hot Tub  ").response == "If it's clean."
    assert Subject.objects.count() == 1


@pytest.mark.django_db
def test_unknown_noun_takes_a_response_from_the_pool():
    Response.objects.create(text="Absolutely not.")

    assert answer_for("aardvark").response == "Absolutely not."


@pytest.mark.django_db
def test_a_claimed_response_leaves_the_pool_but_is_kept():
    Response.objects.create(text="Absolutely not.")

    answer_for("aardvark")

    assert Response.objects.filter(subject__isnull=True).count() == 0
    assert Response.objects.count() == 1, "claimed rows are kept so text stays unique forever"


@pytest.mark.django_db
def test_two_nouns_never_share_a_response():
    Response.objects.create(text="First refusal.")
    Response.objects.create(text="Second refusal.")

    assert answer_for("aardvark").response != answer_for("badger").response


@pytest.mark.django_db
def test_claiming_queues_a_replacement(queue):
    Response.objects.create(text="Absolutely not.")

    answer_for("aardvark")

    assert len(queue.results) == 1


@pytest.mark.django_db
def test_an_empty_pool_falls_back_to_the_hardcoded_list(queue):
    answer = answer_for("aardvark")

    assert "aardvark" in answer.response
    assert queue.results == [], "nothing was taken, so nothing needs replacing"


@pytest.mark.django_db
def test_the_fallback_is_still_linked():
    answer_for("aardvark")

    subject = Subject.objects.select_related("response").get(noun="aardvark")
    assert subject.response.text == answer_for("aardvark").response


@pytest.mark.django_db
def test_repeat_visits_claim_nothing_further(queue):
    Response.objects.create(text="Absolutely not.")
    Response.objects.create(text="Spare one.")

    answer_for("aardvark")
    answer_for("aardvark")
    answer_for("  Aardvark  ")

    assert Response.objects.filter(subject__isnull=True).count() == 1
    assert len(queue.results) == 1


@pytest.mark.django_db
def test_an_answer_is_stable_across_lookups():
    Response.objects.create(text="Absolutely not.")

    assert answer_for("aardvark") == answer_for("aardvark")
    assert Subject.objects.filter(noun="aardvark").count() == 1


@pytest.mark.django_db
def test_save_random_subject_is_idempotent():
    first = save_random_subject("moose")
    second = save_random_subject("moose")

    assert first.pk == second.pk


@pytest.mark.django_db
def test_claim_response_returns_none_when_the_pool_is_empty():
    subject = make("cat", "Old.")

    assert claim_response(subject) is None


@pytest.mark.django_db
def test_claim_response_links_the_subject():
    subject = make("cat", "Old.")
    fresh = Response.objects.create(text="Fresh.")

    assert claim_response(subject) == fresh
    subject.refresh_from_db()
    assert subject.response == fresh


@pytest.mark.parametrize("template", FALLBACKS)
def test_every_fallback_mentions_the_noun(template):
    assert "{noun}" in template


@pytest.mark.parametrize("pk", [1, 2, 3, 17, 400])
def test_case_numbers_are_stable_and_well_formed(pk):
    assert case_number(pk) == case_number(pk), "must not change between renders"
    number, _, letter = case_number(pk).partition("-")
    assert number.isdigit()
    assert letter in "BDFHK"


def test_case_numbers_differ_between_subjects():
    assert case_number(1) != case_number(2)
