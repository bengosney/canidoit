from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from core.answers import answer_for
from core.forms import NounForm


def can_i(request: HttpRequest) -> HttpResponse:
    form = NounForm(request.GET or None)
    answer = answer_for(form.cleaned_data["noun"]) if form.is_valid() else None

    return render(request, "core/can_i.html", {"form": form, "answer": answer})
