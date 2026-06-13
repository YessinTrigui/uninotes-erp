from django.contrib import admin
from .models import Enrollment, Grade, CartItem


class GradeInline(admin.StackedInline):
    model = Grade
    extra = 0
    fields = ('session', 'continuous_assessment', 'final_exam', 'calculated_grade', 'graded_at')
    readonly_fields = ('graded_at',)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'status', 'enrolled_at', 'has_grade')
    list_filter = ('status', 'subject__semester__specialization', 'subject__semester__name')
    search_fields = ('student__username', 'student__first_name', 'student__last_name', 'subject__code', 'subject__name')
    list_editable = ('status',)
    inlines = [GradeInline]
    date_hierarchy = 'enrolled_at'

    def has_grade(self, obj):
        return hasattr(obj, 'grade')
    has_grade.boolean = True
    has_grade.short_description = 'Graded?'


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'session', 'continuous_assessment', 'final_exam', 'calculated_grade', 'is_passing', 'graded_at')
    list_filter = ('session', 'enrollment__subject__semester__specialization')
    search_fields = ('enrollment__student__username', 'enrollment__subject__code')
    readonly_fields = ('graded_at',)

    def is_passing(self, obj):
        return obj.is_passing()
    is_passing.boolean = True
    is_passing.short_description = 'Pass?'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'added_at')
    list_filter = ('subject__semester__specialization', 'subject__semester__name')
    search_fields = ('student__username', 'subject__code', 'subject__name')
    date_hierarchy = 'added_at'
