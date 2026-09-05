from typing import ClassVar

from django.db import models
from django.utils.text import slugify


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
        self.noun = self.noun.strip().lower()
        if not self.slug:
            self.slug = slugify(self.noun)
        super().save(*args, **kwargs)
