from typing import ClassVar

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from core.answers import claim_response
from core.models import Response, Subject
from core.tasks import generate_response


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display: ClassVar[list[str]] = ["noun", "response"]
    search_fields: ClassVar[list[str]] = ["noun", "response__text"]
    list_select_related: ClassVar[list[str]] = ["response"]

    actions: ClassVar[list[str]] = ["requeue"]

    @admin.action(description="Give these a fresh response from the pool")
    def requeue(self, request: HttpRequest, queryset: QuerySet[Subject]) -> None:
        replaced = dry = 0
        for subject in queryset.select_related("response"):
            discarded = subject.response
            if claim_response(subject) is None:
                dry += 1
                continue
            # The old one was rejected, so it does not go back in the pool.
            discarded.delete()
            generate_response.enqueue()
            replaced += 1

        message = f"Replaced {replaced} response(s)."
        if dry:
            message += f" {dry} left alone: the pool is empty."
        self.message_user(request, message)


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display: ClassVar[list[str]] = ["text", "claimed_by", "created"]
    search_fields: ClassVar[list[str]] = ["text"]
    # claimed_by follows the reverse one-to-one, so fetch it with the row.
    list_select_related: ClassVar[list[str]] = ["subject"]

    @admin.display(description="Claimed by")
    def claimed_by(self, response: Response) -> str:
        subject = getattr(response, "subject", None)
        return subject.noun if subject else "-"
