from django.db import models
from django.conf import settings
from catalog.models import Subject


class Enrollment(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_DROPPED = 'dropped'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_DROPPED, 'Dropped'),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'},
        related_name='enrollments',
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='enrollments',
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'subject')
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.student.username} → {self.subject.code} [{self.status}]"


class Grade(models.Model):
    SESSION_MAIN = 'main'
    SESSION_RETAKE = 'retake'

    SESSION_CHOICES = [
        (SESSION_MAIN, 'Main Session'),
        (SESSION_RETAKE, 'Retake Session'),
    ]

    enrollment = models.OneToOneField(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='grade',
    )
    continuous_assessment = models.FloatField(null=True, blank=True)
    final_exam = models.FloatField(null=True, blank=True)
    calculated_grade = models.FloatField(null=True, blank=True)
    session = models.CharField(
        max_length=10,
        choices=SESSION_CHOICES,
        default=SESSION_MAIN,
    )
    graded_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Grade | {self.enrollment.student.username} - {self.enrollment.subject.code} | {self.calculated_grade}"

    def compute_grade(self):
        if self.continuous_assessment is not None and self.final_exam is not None:
            self.calculated_grade = round(
                (self.continuous_assessment * 0.4) + (self.final_exam * 0.6), 2
            )
        elif self.final_exam is not None:
            self.calculated_grade = self.final_exam
        return self.calculated_grade

    def is_passing(self):
        return self.calculated_grade is not None and self.calculated_grade >= 10.0


class CartItem(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'},
        related_name='cart_items',
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='cart_items',
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'subject')
        ordering = ['added_at']

    def __str__(self):
        return f"Cart: {self.student.username} → {self.subject.code}"
