"""Answering "can I ... it?" for a given noun.

`answer_for` is the only entry point the views use. A noun we have no answer
for claims a pre-generated refusal from the pool, which is instant, and queues
a task to replace the one it took. If the pool has run dry it falls back to the
hardcoded list.
"""

import logging
import random
from dataclasses import dataclass
from datetime import datetime

from django.db import connection, transaction

from core.models import Response, Subject, normalise_noun
from core.tasks import generate_response

logger = logging.getLogger(__name__)

# Used only when the pool is empty. Formatted with the noun.
FALLBACKS: list[str] = [
    "No. Not {noun}, not today.",
    "Absolutely not. Put {noun} down.",
    "Out of the question. {noun}? Really?",
    "Never. Step away from {noun}.",
    "Certainly not, and {noun} agrees.",
]


# Cosmetic, from the design: every answer is presented as a filed determination.
CASE_LETTERS = "BDFHK"


def case_number(pk: int) -> str:
    """A stable case reference, so a noun always cites the same one."""
    return f"{4400 + pk * 7}-{CASE_LETTERS[pk % len(CASE_LETTERS)]}"


@dataclass(frozen=True)
class Answer:
    noun: str
    response: str
    case_no: str
    issued: datetime

    @classmethod
    def from_subject(cls, subject: Subject) -> Answer:
        return cls(
            noun=subject.noun,
            response=subject.response.text,
            case_no=case_number(subject.pk),
            issued=subject.response.created,
        )


def _unclaimed():
    """The pool, locked where the database supports it.

    Excludes claimed rows with a subquery rather than `subject__isnull=True`,
    which Django compiles to a LEFT OUTER JOIN: Postgres refuses FOR UPDATE on
    the nullable side of one. SQLite has no FOR UPDATE, so the old join only
    ever failed in production.
    """
    pool = Response.objects.exclude(pk__in=Subject.objects.values("response_id"))
    if connection.features.has_select_for_update:
        pool = pool.select_for_update(skip_locked=connection.features.has_select_for_update_skip_locked)
    return pool


def claim_response(subject: Subject) -> Response | None:
    """Link an unclaimed response to a subject, or None if the pool is empty."""
    with transaction.atomic():
        response = _unclaimed().first()
        if response is None:
            return None
        subject.response = response
        subject.save()
    return response


def save_random_subject(noun: str) -> Subject:
    """Answer an unknown noun from the pool, and queue a replacement.

    Falls back to the hardcoded list when the pool is dry, storing that text as
    its own response row so the link always holds.
    """
    existing = Subject.objects.filter(noun=noun).first()
    if existing is not None:
        return existing

    with transaction.atomic():
        response = _unclaimed().first()
        claimed = response is not None

        if response is None:
            logger.warning("Response pool is empty, falling back to the hardcoded list")
            response, _ = Response.objects.get_or_create(text=random.choice(FALLBACKS).format(noun=noun))

        subject = Subject.objects.create(noun=noun, response=response)

    if claimed:
        generate_response.enqueue()
    return subject


def answer_for(noun: str) -> Answer:
    """The stored answer for a noun, claiming one from the pool if we have none."""
    noun = normalise_noun(noun)
    try:
        subject = Subject.objects.select_related("response").get(noun=noun)
    except Subject.DoesNotExist:
        subject = save_random_subject(noun)
    return Answer.from_subject(subject)
