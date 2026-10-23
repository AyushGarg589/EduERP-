from django.db import migrations, models


def copy_existing_department_links(apps, schema_editor):
    Course = apps.get_model("institute_app", "Course")
    Through = Course.departments.through
    links = [
        Through(course_id=course.pk, department_id=course.legacy_department_id)
        for course in Course.objects.only("pk", "legacy_department_id").iterator()
        if course.legacy_department_id is not None
    ]
    Through.objects.bulk_create(links, ignore_conflicts=True)


class Migration(migrations.Migration):
    dependencies = [
        ("institute_app", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="course",
            old_name="department",
            new_name="legacy_department",
        ),
        migrations.AddField(
            model_name="course",
            name="departments",
            field=models.ManyToManyField(
                related_name="courses",
                to="institute_app.department",
            ),
        ),
        migrations.RunPython(copy_existing_department_links, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="course",
            name="legacy_department",
        ),
    ]
