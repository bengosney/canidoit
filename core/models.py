from typing import ClassVar

from django.db import models

# Long enough for "my next door neighbour", short enough to rule out prose.
MAX_NOUN_LENGTH = 30


class Response(models.Model):
    """A pre-generated refusal, waiting to be claimed by a noun.

    The pool is filled in the background so that answering a visitor never
    waits on the model. A row is claimed by exactly one Subject and then kept,
    so `text` stays unique across everything ever served.
    """

    text = models.TextField(unique=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["created"]

    def __str__(self) -> str:
        return self.text


def normalise_noun(noun: str) -> str:
    """The canonical form of a noun, used for both storage and lookup."""
    return noun.strip().lower()


class Subject(models.Model):
    """A noun someone has asked about, and the response it claimed."""

    noun = models.CharField(max_length=MAX_NOUN_LENGTH, unique=True)
    response = models.OneToOneField(
        Response,
        on_delete=models.PROTECT,
        related_name="subject",
        help_text="The pooled response claimed by this noun.",
    )

    class Meta:
        ordering: ClassVar[list[str]] = ["noun"]

    def __str__(self) -> str:
        return self.noun

    def save(self, *args, **kwargs):
        self.noun = normalise_noun(self.noun)
        super().save(*args, **kwargs)
