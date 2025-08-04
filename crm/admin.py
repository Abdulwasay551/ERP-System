from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import (Partner, Customer, Lead, Opportunity, CommunicationLog, 
                    Campaign, CampaignTarget, SupplierRating, CRMConfiguration)


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
    list_display = ('name', 'company_name', 'email', 'phone', 'status', 'priority', 'assigned_to', 'lead_score', 'created_at')
    search_fields = ('name', 'company_name', 'email', 'phone', 'source', 'status', 'industry')
    list_filter = ('company', 'status', 'priority', 'source', 'assigned_to')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'company_name', 'contact_person', 'company')
        }),
        ('Contact Details', {
            'fields': ('email', 'phone', 'mobile', 'website')
        }),
        ('Address', {
            'fields': ('street', 'city', 'state', 'country')
        }),
        ('Lead Management', {
            'fields': ('source', 'status', 'priority', 'assigned_to', 'lead_score')
        }),
        ('Opportunity Details', {
            'fields': ('estimated_value', 'expected_close_date', 'industry', 'product_interest')
        }),
        ('Requirements & Notes', {
            'fields': ('requirements', 'tags')
        }),
        ('Follow-up', {
            'fields': ('last_contact_date', 'next_follow_up_date', 'follow_up_notes')
        })
    )


@admin.register(Opportunity)
class OpportunityAdmin(ModelAdmin):
    list_display = ('name', 'customer', 'estimated_value', 'stage', 'probability', 'assigned_to', 'expected_close_date', 'created_at')
    search_fields = ('name', 'customer__name', 'stage', 'account__code', 'account__name', 'industry_vertical')
    list_filter = ('company', 'stage', 'priority', 'probability', 'assigned_to')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'company', 'customer', 'lead')
        }),
        ('Opportunity Details', {
            'fields': ('estimated_value', 'stage', 'priority', 'probability', 'assigned_to')
        }),
        ('Timeline', {
            'fields': ('expected_close_date', 'actual_close_date')
        }),
        ('Products & Competition', {
            'fields': ('products_services', 'competitors', 'key_decision_makers')
        }),
        ('Additional Information', {
            'fields': ('budget_confirmed', 'decision_timeline', 'tags', 'industry_vertical')
        }),
        ('Next Steps', {
            'fields': ('next_action', 'next_action_date')
        })
    )


@admin.register(CommunicationLog)
class CommunicationLogAdmin(ModelAdmin):
    list_display = ('type', 'subject', 'get_related_entity_name', 'user', 'status', 'actual_datetime', 'follow_up_required')
    search_fields = ('subject', 'summary', 'detailed_notes', 'customer__name', 'lead__name', 'partner__name', 'user__email')
    list_filter = ('company', 'type', 'direction', 'status', 'follow_up_required')
    
    def get_related_entity_name(self, obj):
        entity = obj.get_related_entity()
        return entity.name if entity else 'No Entity'
    get_related_entity_name.short_description = 'Related Entity'
    
    fieldsets = (
        ('Communication Details', {
            'fields': ('type', 'direction', 'status', 'subject', 'company')
        }),
        ('Related Entities', {
            'fields': ('customer', 'lead', 'opportunity', 'partner')
        }),
        ('Participants', {
            'fields': ('user', 'contact_person', 'participants')
        }),
        ('Timing', {
            'fields': ('scheduled_datetime', 'actual_datetime', 'duration_minutes')
        }),
        ('Content', {
            'fields': ('summary', 'detailed_notes', 'outcome', 'action_items')
        }),
        ('Follow-up', {
            'fields': ('follow_up_required', 'follow_up_date', 'follow_up_notes')
        }),
        ('Attachments & References', {
            'fields': ('attachments', 'reference_number')
        })
    )


@admin.register(Campaign)
class CampaignAdmin(ModelAdmin):
    list_display = ('name', 'campaign_type', 'status', 'start_date', 'end_date', 'budget', 'leads_generated', 'conversions')
    search_fields = ('name', 'description', 'target_audience')
    list_filter = ('company', 'campaign_type', 'status', 'campaign_manager')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'campaign_type', 'status', 'company')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date')
        }),
        ('Targeting', {
            'fields': ('target_audience', 'target_segments')
        }),
        ('Budget & Goals', {
            'fields': ('budget', 'actual_cost', 'target_leads', 'target_revenue', 'target_conversion_rate')
        }),
        ('Content', {
            'fields': ('subject_line', 'message_content', 'call_to_action', 'landing_page_url')
        }),
        ('Results', {
            'fields': ('impressions', 'clicks', 'opens', 'leads_generated', 'conversions', 'revenue_generated'),
            'classes': ('collapse',)
        }),
        ('Management', {
            'fields': ('campaign_manager', 'team_members')
        })
    )


@admin.register(CampaignTarget)
class CampaignTargetAdmin(ModelAdmin):
    list_display = ('campaign', 'get_target_name', 'sent_date', 'opened_date', 'clicked_date', 'responded_date', 'converted_date')
    search_fields = ('campaign__name', 'lead__name', 'customer__name', 'partner__name')
    list_filter = ('campaign', 'response_type')
    
    def get_target_name(self, obj):
        if obj.lead:
            return obj.lead.name
        elif obj.customer:
            return obj.customer.name
        elif obj.partner:
            return obj.partner.name
        return 'Unknown'
    get_target_name.short_description = 'Target'


@admin.register(SupplierRating)
class SupplierRatingAdmin(ModelAdmin):
    list_display = ('supplier', 'overall_rating', 'quality_rating', 'delivery_rating', 'price_rating', 'service_rating', 'rating_date')
    search_fields = ('supplier__partner__name', 'comments')
    list_filter = ('company', 'rating_date', 'rated_by')
    
    fieldsets = (
        ('Rating Information', {
            'fields': ('company', 'supplier', 'rating_period_start', 'rating_period_end')
        }),
        ('Ratings (0-10 Scale)', {
            'fields': ('quality_rating', 'delivery_rating', 'price_rating', 'service_rating', 'communication_rating')
        }),
        ('Comments', {
            'fields': ('comments', 'recommendations')
        }),
        ('Evaluator', {
            'fields': ('rated_by',)
        })
    )


@admin.register(CRMConfiguration)
class CRMConfigurationAdmin(ModelAdmin):
    list_display = ('company', 'email_integration_enabled', 'sms_integration_enabled', 'whatsapp_integration_enabled', 'updated_at')
    search_fields = ('company__name',)
    
    fieldsets = (
        ('Company', {
            'fields': ('company',)
        }),
        ('Lead Configuration', {
            'fields': ('lead_stages', 'lead_assignment_rules', 'lead_scoring_rules')
        }),
        ('Opportunity Configuration', {
            'fields': ('opportunity_stages', 'default_probability_by_stage')
        }),
        ('Customer & Supplier Configuration', {
            'fields': ('customer_categories', 'payment_terms_options', 'supplier_rating_scale', 'supplier_categories')
        }),
        ('Communication Templates', {
            'fields': ('email_templates', 'sms_templates', 'communication_preferences')
        }),
        ('Campaign Configuration', {
            'fields': ('campaign_templates', 'automation_workflows')
        }),
        ('Integration Settings', {
            'fields': ('email_integration_enabled', 'sms_integration_enabled', 'whatsapp_integration_enabled', 'voip_integration_enabled')
        }),
        ('Security & Access', {
            'fields': ('data_sharing_settings', 'role_permissions')
        })
    )
