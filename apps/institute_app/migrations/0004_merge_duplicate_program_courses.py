import re

from django.db import migrations


def normalized_name(value):
    return re.sub(r"[^a-z0-9]", "", (value or "").casefold())


def merge_duplicate_courses(apps, schema_editor):
    Course = apps.get_model("institute_app", "Course")
    Department = apps.get_model("institute_app", "Department")
    StudentEnrollment = apps.get_model("students", "StudentEnrollment")
    database = schema_editor.connection.alias

    groups = {}
    courses = Course.objects.using(database).order_by("campus_id", "pk")
    for course in courses.iterator():
        clean_name = " ".join((course.course_name or "").split()).rstrip(" .")
        course_type = (course.course_type or "").strip().casefold()
        clean_type = {
            "undergraduate": "UG",
            "postgraduate": "PG",
        }.get(course_type, course.course_type)
        if normalized_name(clean_name) in {"btech", "bacheloroftechnology"} and course_type == "regular":
            clean_type = "UG"
        if clean_name != course.course_name or clean_type != course.course_type:
            Course.objects.using(database).filter(pk=course.pk).update(
                course_name=clean_name,
                course_type=clean_type,
            )
            course.course_name = clean_name
            course.course_type = clean_type
        key = (course.campus_id, normalized_name(course.course_name))
        groups.setdefault(key, []).append(course)

    for (_, name_key), duplicates in groups.items():
        if not name_key or len(duplicates) < 2:
            continue

        canonical = duplicates[0]
        duplicate_ids = [course.pk for course in duplicates[1:]]
        all_ids = [canonical.pk, *duplicate_ids]

        Department.objects.using(database).filter(course_id__in=duplicate_ids).update(
            course_id=canonical.pk
        )
        StudentEnrollment.objects.using(database).filter(course_id__in=duplicate_ids).update(
            course_id=canonical.pk
        )

        # Each duplicate course commonly represented a department-specific intake.
        intakes = [course.intake for course in duplicates if course.intake is not None]
        if intakes:
            canonical.intake = sum(intakes)
        canonical.status = any(course.status for course in duplicates)
        canonical.save(using=database, update_fields=["intake", "status"])

        Course.objects.using(database).filter(pk__in=duplicate_ids).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("institute_app", "0003_department_belongs_to_course"),
        ("students", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(merge_duplicate_courses, migrations.RunPython.noop),
    ]
