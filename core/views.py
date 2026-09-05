from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render


def can_i(request: HttpRequest) -> HttpResponseRedirect | HttpResponse:
    return render(request, "core/can_i.html")
