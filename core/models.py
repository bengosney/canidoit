from typing import ClassVar

from django.db import models
from django.utils.text import slugify


def normalise_noun(noun: str) -> str:
    """The canonical form of a noun, used for both storage and lookup."""
    return noun.strip().lower()


class Subject(models.Model):
    class Verdict(models.TextChoices):
        YES = "yes", "Yes"
        NO = "no", "No"
        MAYBE = "maybe", "Maybe"

    noun = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    verdict = models.CharField(max_length=5, choices=Verdict)
    response = models.TextField(help_text="The answer to show, e.g. “only if it's cold”.")

    class Meta:
        ordering: ClassVar[list[str]] = ["noun"]

    def __str__(self) -> str:
        return self.noun

    def save(self, *args, **kwargs):
        self.noun = normalise_noun(self.noun)
        if not self.slug:
            self.slug = self._unique_slug()
        super().save(*args, **kwargs)

    def _unique_slug(self) -> str:
        """A slug for this noun, suffixed if another subject already has it."""
        base = slugify(self.noun) or "subject"
        slug = base
        suffix = 2
        while Subject.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base}-{suffix}"
            suffix += 1
        return slug
