"""Manually top up the pool of pre-generated responses.

Run by hand when the pool looks thin, or to fill it from empty. It only
enqueues jobs, so it returns immediately however slow the model is; the worker
does the generating. Day to day the pool refills itself, since claiming a
response queues its replacement.
"""

from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.tasks.base import TaskResultStatus

from django_tasks_db.models import DBTaskResult

from core.models import Response
from core.tasks import generate_response

DEFAULT_TARGET = 100

TASK_PATH = "core.tasks.generate_response"
IN_FLIGHT = [TaskResultStatus.READY, TaskResultStatus.RUNNING]


def in_flight() -> int:
    """Jobs already queued or running, so running this twice doesn't double up."""
    return DBTaskResult.objects.filter(task_path=TASK_PATH, status__in=IN_FLIGHT).count()


class Command(BaseCommand):
    help = "Queue jobs to bring the response pool up to its target size."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--target",
            type=int,
            default=DEFAULT_TARGET,
            help=f"Pool size to aim for, counting jobs already queued (default: {DEFAULT_TARGET}).",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        pool = Response.objects.count()
        queued_already = in_flight()
        shortfall = options["target"] - pool - queued_already

        if shortfall <= 0:
            self.stdout.write(f"Pool has {pool}, with {queued_already} on the way. Nothing to do.")
            return

        for _ in range(shortfall):
            generate_response.enqueue()

        self.stdout.write(
            self.style.SUCCESS(
                f"queued {shortfall} job(s); pool {pool}, in flight {queued_already + shortfall}, "
                f"target {options['target']}"
            )
        )
