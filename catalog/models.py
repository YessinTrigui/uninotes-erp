from django.db import models
from django.conf import settings


class Specialization(models.Model):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=15, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class Semester(models.Model):
    SEMESTER_CHOICES = [
        ('S1', 'Semester 1'),
        ('S2', 'Semester 2'),
        ('S3', 'Semester 3'),
        ('S4', 'Semester 4'),
        ('S5', 'Semester 5'),
        ('S6', 'Semester 6'),
    ]

    specialization = models.ForeignKey(
        Specialization,
        on_delete=models.CASCADE,
        related_name='semesters',
    )
    name = models.CharField(max_length=5, choices=SEMESTER_CHOICES)
    academic_year = models.CharField(max_length=9)
    credit_limit = models.PositiveIntegerField(default=30)

    class Meta:
        unique_together = ('specialization', 'name', 'academic_year')
        ordering = ['specialization', 'name']

    def __str__(self):
        return f"{self.specialization.code} | {self.name} ({self.academic_year})"


class Subject(models.Model):
    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
        related_name='subjects',
    )
    responsible_tutor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'tutor'},
        related_name='taught_subjects',
    )
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    credits = models.PositiveIntegerField()
    coefficient = models.FloatField(default=1.0)
    max_students = models.PositiveIntegerField(default=30)
    is_mandatory = models.BooleanField(default=True)

    class Meta:
        ordering = ['semester', 'name']

    def __str__(self):
        return f"{self.code} - {self.name} ({self.credits} cr.)"

    def enrolled_count(self):
        return self.enrollments.filter(status='confirmed').count()

    def has_available_seats(self):
        return self.enrolled_count() < self.max_students
