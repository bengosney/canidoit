from django.conf import settings


def site_verb(request):
    """Expose the site's verb as a variable, e.g. the "do" in "can I do it?"."""
    return {"site_verb": settings.SITE_VERB}
