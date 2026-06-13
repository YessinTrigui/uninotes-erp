from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'student_id', 'current_semester', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_active', 'current_semester__specialization')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('UniNotes Profile', {'fields': ('role', 'student_id', 'phone_number', 'current_semester')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('UniNotes Profile', {'fields': ('role', 'student_id', 'phone_number', 'current_semester')}),
    )
    search_fields = ('username', 'email', 'student_id', 'first_name', 'last_name')
    ordering = ('username',)


admin.site.register(User, UserAdmin)
