from django.db import migrations, models
import django.db.models.deletion


def move_departments_under_courses(apps, schema_editor):
    Course = apps.get_model("institute_app", "Course")
    Department = apps.get_model("institute_app", "Department")
    # The newly added Department.course FK also creates a reverse
    # `Course.departments` relation, shadowing the old M2M descriptor while
    # this migration state is rendered. Read the historical join model by name.
    Through = apps.get_model("institute_app", "Course_departments")

    for department in Department.objects.only("pk", "campus_id").iterator():
        linked_course_ids = Through.objects.filter(
            department_id=department.pk
        ).values_list("course_id", flat=True)
        course_id = Course.objects.filter(
            pk__in=linked_course_ids,
            campus_id=department.campus_id,
        ).order_by("pk").values_list("pk", flat=True).first()
        if course_id is None:
            course_id = Course.objects.filter(
                pk__in=linked_course_ids,
            ).order_by("pk").values_list("pk", flat=True).first()
        if course_id is not None:
            Department.objects.filter(pk=department.pk).update(course_id=course_id)


class Migration(migrations.Migration):
    dependencies = [
        ("institute_app", "0002_course_departments_many_to_many"),
    ]

    operations = [
        migrations.AddField(
            model_name="department",
            name="course",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="departments",
                to="institute_app.course",
            ),
        ),
        migrations.RunPython(move_departments_under_courses, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="course",
            name="departments",
        ),
        migrations.RemoveField(
            model_name="department",
            name="campus",
        ),
    ]
