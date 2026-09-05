from django import forms

from core.models import Subject, normalise_noun


class NounForm(forms.Form):
    noun = forms.CharField(
        max_length=Subject._meta.get_field("noun").max_length,
        label="",
        widget=forms.TextInput(attrs={"placeholder": "a thing", "autofocus": True, "autocomplete": "off"}),
    )

    def clean_noun(self) -> str:
        return normalise_noun(self.cleaned_data["noun"])
