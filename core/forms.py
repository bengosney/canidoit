from django import forms
from django.core.exceptions import ValidationError

from core import profanity
from core.models import Subject, normalise_noun


class NounForm(forms.Form):
    noun = forms.CharField(
        max_length=Subject._meta.get_field("noun").max_length,
        label="",
        widget=forms.TextInput(attrs={"placeholder": "a thing", "autofocus": True, "autocomplete": "off"}),
    )

    def clean_noun(self) -> str:
        noun = normalise_noun(self.cleaned_data["noun"])
        if profanity.is_profane(noun):
            raise ValidationError("Keep it clean.")
        return noun
