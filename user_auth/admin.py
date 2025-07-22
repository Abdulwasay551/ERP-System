from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from unfold.admin import ModelAdmin
from .models import User, Company, Role, ActivityLog

# Register your models here.

@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    list_display = ('email', 'first_name', 'last_name', 'company', 'role', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'company', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'company', 'role', 'is_staff', 'is_active'),
        }),
    )

@admin.register(Company)
class CompanyAdmin(ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    search_fields = ('name',)
    list_filter = ('is_active',)


@admin.register(ActivityLog)
class ActivityLogAdmin(ModelAdmin):
    list_display = ('user', 'action', 'ip_address', 'created_at')
    search_fields = ('user__email', 'action', 'details')
    list_filter = ('action',)

@admin.register(Role)
class RoleAdmin(ModelAdmin):
    list_display = ('name', 'department', 'level', 'parent', 'is_active')
    search_fields = ('name', 'department')
    list_filter = ('department', 'level', 'is_active')