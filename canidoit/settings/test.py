from canidoit.settings.dev import *  # noqa

# Tests never talk to a model, and never run a queued task implicitly.
LLM_ENABLED = False

TASKS = {
    "default": {
        "BACKEND": "django.tasks.backends.dummy.DummyBackend",
    },
}
