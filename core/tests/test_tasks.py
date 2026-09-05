import pytest

from core.models import Response
from core.tasks import generate_response


@pytest.mark.django_db
def test_a_usable_reply_joins_the_pool(mocker):
    mocker.patch("core.tasks.llm.generate", return_value="Absolutely not.")

    generate_response.func()

    assert list(Response.objects.values_list("text", flat=True)) == ["Absolutely not."]


@pytest.mark.django_db
def test_an_unusable_reply_adds_nothing(mocker):
    mocker.patch("core.tasks.llm.generate", return_value=None)

    generate_response.func()

    assert Response.objects.count() == 0


@pytest.mark.django_db
def test_a_repeated_reply_does_not_duplicate(mocker):
    mocker.patch("core.tasks.llm.generate", return_value="Absolutely not.")

    generate_response.func()
    generate_response.func()

    assert Response.objects.count() == 1
