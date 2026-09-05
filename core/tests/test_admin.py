from django.contrib.admin.sites import AdminSite

import pytest

from core.admin import ResponseAdmin, SubjectAdmin
from core.models import Response, Subject

NOUNS = ["cat", "moose", "badger"]


@pytest.fixture
def modeladmin():
    admin = SubjectAdmin(Subject, AdminSite())
    admin.message_user = lambda *a, **k: None
    return admin


def make(noun):
    return Subject.objects.create(noun=noun, response=Response.objects.create(text=f"Old answer for {noun}."))


@pytest.mark.django_db
def test_requeue_swaps_in_a_pooled_response(modeladmin, queue, rf):
    subject = make("cat")
    Response.objects.create(text="A fresh refusal.")

    modeladmin.requeue(rf.post("/admin/"), Subject.objects.filter(pk=subject.pk))

    subject.refresh_from_db()
    assert subject.response.text == "A fresh refusal."
    assert Response.objects.filter(subject__isnull=True).count() == 0
    assert not Response.objects.filter(text="Old answer for cat.").exists(), "the rejected one is discarded"


@pytest.mark.django_db
def test_requeue_queues_a_replacement(modeladmin, queue, rf):
    subject = make("cat")
    Response.objects.create(text="A fresh refusal.")

    modeladmin.requeue(rf.post("/admin/"), Subject.objects.filter(pk=subject.pk))

    assert len(queue.results) == 1


@pytest.mark.django_db
def test_requeue_leaves_rows_alone_when_the_pool_is_empty(modeladmin, queue, rf):
    subject = make("cat")

    modeladmin.requeue(rf.post("/admin/"), Subject.objects.filter(pk=subject.pk))

    subject.refresh_from_db()
    assert subject.response.text == "Old answer for cat."
    assert queue.results == []


@pytest.mark.django_db
def test_requeue_handles_several_at_once(modeladmin, queue, rf):
    for noun in NOUNS:
        make(noun)
    for i in range(len(NOUNS)):
        Response.objects.create(text=f"Refusal {i}.")

    modeladmin.requeue(rf.post("/admin/"), Subject.objects.all())

    assert Response.objects.filter(subject__isnull=True).count() == 0
    assert len(queue.results) == len(NOUNS)
    assert Subject.objects.filter(response__text__startswith="Refusal").count() == len(NOUNS)


@pytest.mark.django_db
def test_response_changelist_does_not_query_per_row(django_assert_num_queries, rf, admin_user):
    for i in range(5):
        Subject.objects.create(noun=f"noun{i}", response=Response.objects.create(text=f"Refusal {i}."))

    modeladmin = ResponseAdmin(Response, AdminSite())
    request = rf.get("/admin/")
    request.user = admin_user

    changelist = modeladmin.get_changelist_instance(request)
    with django_assert_num_queries(1):
        claimed = [modeladmin.claimed_by(r) for r in changelist.get_queryset(request)]

    assert sorted(claimed) == [f"noun{i}" for i in range(5)]
