from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def site_verb():
    """The site's verb, e.g. the "do" in "can I do it?"."""
    return settings.SITE_VERB
