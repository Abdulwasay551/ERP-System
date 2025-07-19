from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Customer, Lead, Opportunity, CommunicationLog

@admin.register(Customer)
class CustomerAdmin(ModelAdmin):
    list_display = ('name', 'company', 'email', 'phone', 'created_by', 'created_at')
    search_fields = ('name', 'email', 'phone', 'address')
    list_filter = ('company',)

@admin.register(Lead)
class LeadAdmin(ModelAdmin):
    list_display = ('name', 'company', 'email', 'phone', 'status', 'assigned_to', 'created_at')
    search_fields = ('name', 'email', 'phone', 'source', 'status')
    list_filter = ('company', 'status')

@admin.register(Opportunity)
class OpportunityAdmin(ModelAdmin):
    list_display = ('name', 'company', 'customer', 'value', 'stage', 'assigned_to', 'close_date', 'created_at')
    search_fields = ('name', 'customer__name', 'stage')
    list_filter = ('company', 'stage')

@admin.register(CommunicationLog)
class CommunicationLogAdmin(ModelAdmin):
    list_display = ('type', 'company', 'customer', 'user', 'subject', 'timestamp')
    search_fields = ('subject', 'notes', 'customer__name', 'user__email')
    list_filter = ('company', 'type')
