"""Turn Subject.response from copied text into a link to a pooled Response.

Existing answers are preserved: each subject's text becomes a Response row it
claims. Where two subjects happened to share the same text they cannot both
claim it, since text is unique and the link is one-to-one, so the later ones
take an unclaimed row from the pool instead.
"""

from django.db import migrations, models
import django.db.models.deletion


def link_existing_answers(apps, schema_editor):
    Response = apps.get_model("core", "Response")
    Subject = apps.get_model("core", "Subject")

    for subject in Subject.objects.order_by("pk"):
        response, created = Response.objects.get_or_create(text=subject.old_response)
        taken = not created and Subject.objects.filter(response_link=response).exists()

        if taken:
            response = Response.objects.filter(response_link__isnull=True).first()
            if response is None:
                response = Response.objects.create(text=f"{subject.old_response} ({subject.noun})")

        subject.response_link = response
        subject.save(update_fields=["response_link"])


def unlink(apps, schema_editor):
    Subject = apps.get_model("core", "Subject")
    for subject in Subject.objects.select_related("response_link"):
        subject.old_response = subject.response_link.text
        subject.save(update_fields=["old_response"])


class Migration(migrations.Migration):
    dependencies = [("core", "0003_response")]

    operations = [
        migrations.RemoveField(model_name="subject", name="slug"),
        migrations.RenameField(model_name="subject", old_name="response", new_name="old_response"),
        migrations.AddField(
            model_name="subject",
            name="response_link",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="response_link",
                to="core.response",
            ),
        ),
        migrations.RunPython(link_existing_answers, unlink),
        migrations.RemoveField(model_name="subject", name="old_response"),
        migrations.RenameField(model_name="subject", old_name="response_link", new_name="response"),
        migrations.AlterField(
            model_name="subject",
            name="response",
            field=models.OneToOneField(
                help_text="The pooled response claimed by this noun.",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="subject",
                to="core.response",
            ),
        ),
    ]
