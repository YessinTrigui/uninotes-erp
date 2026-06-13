from django.contrib import admin
from .models import Specialization, Semester, Subject


class SubjectInline(admin.TabularInline):
    model = Subject
    extra = 1
    fields = ('code', 'name', 'credits', 'coefficient', 'is_mandatory', 'max_students', 'responsible_tutor')
    show_change_link = True


class SemesterInline(admin.TabularInline):
    model = Semester
    extra = 1
    fields = ('name', 'academic_year', 'credit_limit')
    show_change_link = True


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'semester_count')
    search_fields = ('code', 'name')
    inlines = [SemesterInline]

    def semester_count(self, obj):
        return obj.semesters.count()
    semester_count.short_description = 'Semesters'


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'specialization', 'name', 'academic_year', 'credit_limit', 'subject_count')
    list_filter = ('specialization', 'name', 'academic_year')
    search_fields = ('specialization__name', 'academic_year')
    inlines = [SubjectInline]

    def subject_count(self, obj):
        return obj.subjects.count()
    subject_count.short_description = 'Subjects'


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'semester', 'credits', 'coefficient', 'is_mandatory', 'responsible_tutor', 'enrolled_count', 'max_students')
    list_filter = ('semester__specialization', 'semester__name', 'is_mandatory')
    search_fields = ('code', 'name', 'responsible_tutor__username')
    list_editable = ('is_mandatory',)

    def enrolled_count(self, obj):
        return obj.enrolled_count()
    enrolled_count.short_description = 'Enrolled'
