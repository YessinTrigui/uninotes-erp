from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_STUDENT = 'student'
    ROLE_TUTOR = 'tutor'
    ROLE_ADMIN = 'admin'

    ROLE_CHOICES = [
        (ROLE_STUDENT, 'Student'),
        (ROLE_TUTOR, 'Tutor'),
        (ROLE_ADMIN, 'Admin'),
    ]

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=ROLE_STUDENT,
    )

    student_id = models.CharField(max_length=20, blank=True, null=True, unique=True)

    phone_number = models.CharField(max_length=20, blank=True, null=True)

    current_semester = models.ForeignKey(
        'catalog.Semester',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
    )

    def is_student(self):
        return self.role == self.ROLE_STUDENT

    def is_tutor(self):
        return self.role == self.ROLE_TUTOR

    def is_admin_user(self):
        return self.role == self.ROLE_ADMIN

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"
