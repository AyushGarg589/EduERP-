from django.conf import settings
from django.db.models import Q
from django.http import Http404
from django.views.static import serve

from apps.faculty.models import Faculty
from apps.institute_app.tenancy import get_user_institute
from apps.students.models import DocumentDetails, Student


def institute_media(request, path):
    institute = get_user_institute(request.user)
    if institute is None:
        return serve(request, path, document_root=settings.MEDIA_ROOT)

    faculty_file = Faculty.objects.filter(
        profile_photo=path,
        campus__institute=institute,
    ).exists()
    student_file = Student.objects.filter(
        profile_photo=path,
        campus__institute=institute,
    ).exists()
    document_file = DocumentDetails.objects.filter(
        student__campus__institute=institute,
    ).filter(
        Q(marksheet_10=path)
        | Q(marksheet_12=path)
        | Q(aadhaar=path)
        | Q(migration_certificate=path)
        | Q(certificate=path)
    ).exists()

    if not (faculty_file or student_file or document_file):
        raise Http404

    return serve(request, path, document_root=settings.MEDIA_ROOT)
