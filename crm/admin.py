from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Partner, Customer, Lead, Opportunity, CommunicationLog


@admin.register(Partner)
class PartnerAdmin(ModelAdmin):
    list_display = ('name', 'display_name', 'partner_type', 'email', 'phone', 'is_customer', 'is_supplier', 'is_employee', 'is_active')
    search_fields = ('name', 'display_name', 'email', 'phone', 'company_name', 'tax_id')
    list_filter = ('company', 'partner_type', 'is_customer', 'is_supplier', 'is_employee', 'is_project_stakeholder', 'is_lead', 'is_active')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'display_name', 'partner_type', 'company', 'image')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'mobile', 'website')
        }),
        ('Address', {
            'fields': ('street', 'street2', 'city', 'state', 'zip_code', 'country')
        }),
        ('Business Information', {
            'fields': ('company_name', 'tax_id', 'registration_number')
        }),
        ('Partner Roles', {
            'fields': ('is_customer', 'is_supplier', 'is_employee', 'is_project_stakeholder', 'is_lead'),
            'description': 'Select the roles this partner can fulfill'
        }),
        ('Financial', {
            'fields': ('payment_terms', 'credit_limit'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('notes', 'is_active', 'created_by'),
            'classes': ('collapse',)
        })
    )


@admin.register(Customer)
class CustomerAdmin(ModelAdmin):
    list_display = ('name', 'company', 'email', 'phone', 'account', 'created_by', 'created_at')
    search_fields = ('name', 'email', 'phone', 'address', 'account__code', 'account__name')
    list_filter = ('company', 'account')


@admin.register(Lead)
class LeadAdmin(ModelAdmin):
    list_display = ('name', 'company', 'email', 'phone', 'status', 'assigned_to', 'created_at')
    search_fields = ('name', 'email', 'phone', 'source', 'status')
    list_filter = ('company', 'status')


@admin.register(Opportunity)
class OpportunityAdmin(ModelAdmin):
    list_display = ('name', 'company', 'customer', 'account', 'value', 'stage', 'assigned_to', 'close_date', 'created_at')
    search_fields = ('name', 'customer__name', 'stage', 'account__code', 'account__name')
    list_filter = ('company', 'stage', 'account')


@admin.register(CommunicationLog)
class CommunicationLogAdmin(ModelAdmin):
    list_display = ('type', 'company', 'customer', 'user', 'subject', 'timestamp')
    search_fields = ('subject', 'notes', 'customer__name', 'user__email')
    list_filter = ('company', 'type')
