from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Customer, Lead, Opportunity, CommunicationLog

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
