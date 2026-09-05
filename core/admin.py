from typing import ClassVar

from django.contrib import admin

from core.models import Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display: ClassVar[list[str]] = ["noun", "verdict"]
    list_filter: ClassVar[list[str]] = ["verdict"]
    search_fields: ClassVar[list[str]] = ["noun", "response"]
    prepopulated_fields: ClassVar[dict[str, list[str]]] = {"slug": ["noun"]}
