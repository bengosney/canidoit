from django.core.management import call_command

import pytest

from core.models import Response

TARGET = 5


@pytest.mark.django_db
def test_jobs_are_queued_for_the_whole_shortfall(queue):
    call_command("topup_responses", "--target", str(TARGET))

    assert len(queue.results) == TARGET


@pytest.mark.django_db
def test_existing_responses_reduce_the_shortfall(queue):
    Response.objects.create(text="Already here.")

    call_command("topup_responses", "--target", str(TARGET))

    assert len(queue.results) == TARGET - 1


@pytest.mark.django_db
def test_a_full_pool_queues_nothing(queue):
    Response.objects.create(text="Already here.")

    call_command("topup_responses", "--target", "1")

    assert queue.results == []


@pytest.mark.django_db
def test_the_command_never_calls_the_model(mocker, queue):
    generate = mocker.patch("core.llm.generate")

    call_command("topup_responses", "--target", str(TARGET))

    generate.assert_not_called()


@pytest.mark.django_db
def test_jobs_already_in_flight_are_not_duplicated(mocker, queue):
    mocker.patch("core.management.commands.topup_responses.in_flight", return_value=TARGET)

    call_command("topup_responses", "--target", str(TARGET))

    assert queue.results == [], "running it twice must not double up jobs"
