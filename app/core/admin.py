from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from core import models

class UserAdmin(BaseUserAdmin):
    ordering = ('id',)
    list_display = ('email', 'name','is_active',)

    search_fields = ('email', 'name',)
    list_filter = ('is_active',)
    readonly_fields = ('email','last_login',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('last_login', 'name', 'is_active', 'is_staff','is_superuser',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'name', 'is_active', 'is_staff', 'is_superuser',)
        }),
    )
admin.site.register(models.User, UserAdmin)