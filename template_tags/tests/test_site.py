from django.template import Context, Template
from django.template.loader import render_to_string

import pytest

from template_tags.context_processors import site_verb as site_verb_context
from template_tags.templatetags.site import site_verb


def test_site_verb_defaults_to_do():
    assert site_verb() == "do"


@pytest.mark.parametrize("verb", ["do", "fix", "eat"])
def test_site_verb_follows_setting(settings, verb):
    settings.SITE_VERB = verb
    assert site_verb() == verb


def test_context_processor_exposes_verb(settings, rf):
    settings.SITE_VERB = "ride"
    assert site_verb_context(rf.get("/")) == {"site_verb": "ride"}


def test_verb_is_filterable_in_templates(settings, rf):
    settings.SITE_VERB = "ride"
    template = Template("Can I {{ site_verb|title }} it?")
    context = Context(site_verb_context(rf.get("/")))
    assert template.render(context) == "Can I Ride it?"


def test_tag_renders_after_load(settings):
    settings.SITE_VERB = "ride"
    template = Template("{% load site %}Can I {% site_verb %} it?")
    assert template.render(Context()) == "Can I ride it?"


def test_base_html_title_renders(settings, rf):
    settings.SITE_VERB = "do"
    html = render_to_string("base_html.html", request=rf.get("/"))
    assert "<title>Can I Do it?</title>" in html
