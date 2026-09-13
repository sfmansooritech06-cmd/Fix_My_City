from django.contrib import admin
from .models import User, Citizen, Officer


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_active')
    list_filter = ('role', 'is_active')
    search_fields = ('username', 'email')


@admin.register(Citizen)
class CitizenAdmin(admin.ModelAdmin):
    list_display = ('citizen_id', 'full_name', 'phone', 'user')
    search_fields = ('citizen_id', 'full_name', 'phone')


@admin.register(Officer)
class OfficerAdmin(admin.ModelAdmin):
    list_display = (
        'employee_id',
        'full_name',
        'department',
        'phone',
        'is_approved',
    )
    list_filter = ('department', 'is_approved')
    search_fields = ('employee_id', 'full_name', 'phone')