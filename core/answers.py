"""Answering "can I ... it?" for a given noun.

`answer_for` is the only entry point the views use. Nouns we have no answer for
get one invented by `save_random_subject`, which is a placeholder meant to be
replaced; invented answers are stored so the same noun keeps the same answer.
"""

import random
from dataclasses import dataclass

from core.models import Subject, normalise_noun

# Placeholder responses, pending something better. Each is a (verdict, template)
# pair; the template is formatted with the noun.
FALLBACKS: list[tuple[str, str]] = [
    (Subject.Verdict.YES, "Yes, {noun} is fair game."),
    (Subject.Verdict.YES, "Go on then, {noun} it is."),
    (Subject.Verdict.NO, "No. Not {noun}, not today."),
    (Subject.Verdict.NO, "Absolutely not. Put {noun} down."),
    (Subject.Verdict.MAYBE, "Maybe, but have a long think about {noun} first."),
    (Subject.Verdict.MAYBE, "{noun}? Ask again when you're sober."),
]


@dataclass(frozen=True)
class Answer:
    noun: str
    verdict: str
    response: str

    @property
    def get_verdict_display(self) -> str:
        return Subject.Verdict(self.verdict).label

    @classmethod
    def from_subject(cls, subject: Subject) -> Answer:
        return cls(noun=subject.noun, verdict=subject.verdict, response=subject.response)


def save_random_subject(noun: str) -> Subject:
    """Invent an answer for an unknown noun and remember it."""
    verdict, template = random.choice(FALLBACKS)
    subject, _ = Subject.objects.get_or_create(
        noun=noun,
        defaults={"verdict": verdict, "response": template.format(noun=noun)},
    )
    return subject


def answer_for(noun: str) -> Answer:
    """The stored answer for a noun, inventing and saving one if we have none."""
    noun = normalise_noun(noun)
    try:
        subject = Subject.objects.get(noun=noun)
    except Subject.DoesNotExist:
        subject = save_random_subject(noun)
    return Answer.from_subject(subject)
