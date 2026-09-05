from http import HTTPStatus

from django.urls import reverse

import pytest

from core.models import Subject


@pytest.mark.django_db
def test_get_without_a_noun_shows_an_empty_form(client):
    response = client.get(reverse("core:can_i"))

    assert response.status_code == HTTPStatus.OK
    assert response.context["answer"] is None
    assert not response.context["form"].is_bound


@pytest.mark.django_db
def test_known_noun_shows_the_stored_response(client):
    Subject.objects.create(noun="cat", verdict=Subject.Verdict.NO, response="Obviously not.")

    response = client.get(reverse("core:can_i"), {"noun": "Cat"})

    assert "Obviously not." in response.content.decode()


@pytest.mark.django_db
def test_unknown_noun_shows_a_guessed_response(client):
    response = client.get(reverse("core:can_i"), {"noun": "aardvark"})

    assert "aardvark" in response.content.decode()


@pytest.mark.django_db
def test_blank_noun_shows_an_error_and_no_answer(client):
    response = client.get(reverse("core:can_i"), {"noun": ""})

    assert response.context["answer"] is None
    assert response.context["form"].errors


@pytest.mark.django_db
def test_htmx_request_returns_only_the_fragment(client):
    response = client.get(reverse("core:can_i"), {"noun": "cat"}, headers={"hx-request": "true"})
    body = response.content.decode()

    assert "<html" not in body
    assert 'id="can-i"' in body


@pytest.mark.django_db
def test_unknown_noun_is_persisted_by_the_view(client):
    client.get(reverse("core:can_i"), {"noun": "aardvark"})

    assert Subject.objects.filter(noun="aardvark").exists()
