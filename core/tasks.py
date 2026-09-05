"""Background top-up of the pool of pre-generated responses."""

import logging

from django.tasks import task

from core import llm
from core.models import Response

logger = logging.getLogger(__name__)


@task()
def generate_response() -> None:
    """Add one refusal to the pool.

    Queued whenever a response is claimed, so the pool replenishes itself as
    it is used. A model that fumbles or repeats itself simply adds nothing;
    the cron top-up is the backstop.
    """
    text = llm.generate()
    if text is None:
        return

    _, created = Response.objects.get_or_create(text=text)
    if not created:
        logger.info("Model repeated an existing response, pool unchanged: %r", text[:50])
