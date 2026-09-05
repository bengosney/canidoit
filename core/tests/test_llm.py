import json

import pytest
import requests

from core import llm


@pytest.fixture
def enabled(settings):
    settings.LLM_ENABLED = True
    settings.LLM_BASE_URL = "http://model.invalid:11434"
    settings.LLM_MODEL = "test-model"
    settings.LLM_TIMEOUT = 5


def fake_post(mocker, *, payload=None, exc=None):
    if exc is not None:
        return mocker.patch("core.llm.requests.post", side_effect=exc)
    reply = mocker.Mock()
    reply.raise_for_status.return_value = None
    reply.json.return_value = {"response": payload}
    return mocker.patch("core.llm.requests.post", return_value=reply)


def test_disabled_returns_none_without_calling_out(mocker, settings):
    settings.LLM_ENABLED = False
    post = fake_post(mocker, payload="{}")

    assert llm.generate() is None
    post.assert_not_called()


def test_valid_reply_is_returned(mocker, enabled):
    fake_post(mocker, payload=json.dumps({"response": "  Leave it alone.  "}))

    assert llm.generate() == "Leave it alone."


def test_the_prompt_is_a_constant_with_nothing_interpolated(mocker, enabled, settings):
    """The model must have no opportunity to comment on what was asked."""
    settings.SITE_VERB = "ride"
    fake_post(mocker, payload=json.dumps({"response": "No chance."}))

    llm.generate()

    body = requests.post.call_args.kwargs["json"]
    assert body["prompt"] == llm.PROMPT
    assert "ride" not in body["prompt"]
    assert "{" not in body["prompt"].replace('{"response"', "")


def test_schema_asks_only_for_the_sentence():
    assert list(llm.SCHEMA["properties"]) == ["response"]


def test_timeout_returns_none(mocker, enabled):
    fake_post(mocker, exc=requests.Timeout("too slow"))

    assert llm.generate() is None


def test_connection_error_returns_none(mocker, enabled):
    fake_post(mocker, exc=requests.ConnectionError("no route"))

    assert llm.generate() is None


def test_truncated_json_returns_none(mocker, enabled):
    fake_post(mocker, payload='{"response": "half a sen')

    assert llm.generate() is None


def test_empty_response_is_discarded(mocker, enabled):
    fake_post(mocker, payload=json.dumps({"response": "   "}))

    assert llm.generate() is None


@pytest.mark.parametrize(
    "response",
    [
        "Of course, I'd love to, but I'm not sure it's the time.",
        "Let me have it, but only if you are brave.",
        "It's not for me to judge.",
        "We should probably not.",
    ],
)
def test_answers_about_itself_are_discarded(mocker, enabled, response):
    fake_post(mocker, payload=json.dumps({"response": response}))

    assert llm.generate() is None


@pytest.mark.parametrize(
    "response",
    ["No fucking way.", "Certainly not, you absolute bastard.", "That would be a screw too far."],
)
def test_crude_answers_are_discarded(mocker, enabled, response):
    """Scored by alt-profanity-check, so these are its real judgements."""
    fake_post(mocker, payload=json.dumps({"response": response}))

    assert llm.generate() is None


def test_a_profane_answer_is_discarded(mocker, enabled):
    fake_post(mocker, payload=json.dumps({"response": "Borderline."}))
    mocker.patch("core.llm.profanity.is_profane", return_value=True)

    assert llm.generate() is None


def test_a_clean_answer_passes(mocker, enabled):
    fake_post(mocker, payload=json.dumps({"response": "Borderline."}))
    mocker.patch("core.llm.profanity.is_profane", return_value=False)

    assert llm.generate() == "Borderline."


@pytest.mark.parametrize(
    "response",
    [
        "Absolutely not. Have a long think about your choices.",
        "No. Put it down and walk away slowly.",
        "Out of the question, and you know exactly why.",
    ],
)
def test_clean_third_person_answers_are_kept(mocker, enabled, response):
    fake_post(mocker, payload=json.dumps({"response": response}))

    assert llm.generate() == response


def test_overlong_response_is_truncated(mocker, enabled):
    fake_post(mocker, payload=json.dumps({"response": "x" * 1000}))

    assert len(llm.generate()) == llm.MAX_RESPONSE_LENGTH


def test_one_call_per_invocation(mocker, enabled):
    ask = mocker.patch("core.llm._ask", return_value=json.dumps({"response": "I'd love to."}))

    assert llm.generate() is None
    assert ask.call_count == 1, "retrying is the caller's job, not this function's"
