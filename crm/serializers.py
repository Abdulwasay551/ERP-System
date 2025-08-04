from rest_framework import serializers
from .models import (Customer, Lead, Opportunity, CommunicationLog, Partner, 
                    Campaign, CampaignTarget, SupplierRating, CRMConfiguration)


class PartnerSerializer(serializers.ModelSerializer):
    """Serializer for Partner model"""
    full_address = serializers.CharField(source='get_full_address', read_only=True)
    
    class Meta:
        model = Partner
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class CustomerSerializer(serializers.ModelSerializer):
    """Enhanced Customer serializer with partner relationship"""
    partner_details = PartnerSerializer(source='partner', read_only=True)
    
    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class LeadSerializer(serializers.ModelSerializer):
    """Enhanced Lead serializer with conversion tracking"""
    converted_customer_name = serializers.CharField(source='converted_to_customer.name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    days_since_creation = serializers.SerializerMethodField()
    
    class Meta:
        model = Lead
        fields = '__all__'
        read_only_fields = ('converted_to_customer', 'conversion_date', 'created_at', 'updated_at')
    
    def get_days_since_creation(self, obj):
        from django.utils import timezone
        if obj.created_at:
            return (timezone.now().date() - obj.created_at.date()).days
        return 0


class OpportunitySerializer(serializers.ModelSerializer):
    """Enhanced Opportunity serializer with calculations"""
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    weighted_value = serializers.DecimalField(source='get_weighted_value', max_digits=15, decimal_places=2, read_only=True)
    stage_display = serializers.CharField(source='get_stage_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = Opportunity
        fields = '__all__'
        read_only_fields = ('stage_history', 'actual_close_date', 'created_at', 'updated_at')


class CommunicationLogSerializer(serializers.ModelSerializer):
    """Enhanced Communication Log serializer"""
    related_entity_name = serializers.SerializerMethodField()
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    direction_display = serializers.CharField(source='get_direction_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = CommunicationLog
        fields = '__all__'
        read_only_fields = ('timestamp', 'updated_at')
    
    def get_related_entity_name(self, obj):
        entity = obj.get_related_entity()
        return entity.name if entity else None


class CampaignSerializer(serializers.ModelSerializer):
    """Campaign serializer with performance metrics"""
    campaign_manager_name = serializers.CharField(source='campaign_manager.get_full_name', read_only=True)
    team_member_names = serializers.SerializerMethodField()
    click_through_rate = serializers.DecimalField(source='get_click_through_rate', max_digits=5, decimal_places=2, read_only=True)
    conversion_rate = serializers.DecimalField(source='get_conversion_rate', max_digits=5, decimal_places=2, read_only=True)
    roi = serializers.DecimalField(source='get_roi', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Campaign
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'cost_per_lead')
    
    def get_team_member_names(self, obj):
        return [member.get_full_name() for member in obj.team_members.all()]


class CampaignTargetSerializer(serializers.ModelSerializer):
    """Campaign Target serializer"""
    campaign_name = serializers.CharField(source='campaign.name', read_only=True)
    target_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CampaignTarget
        fields = '__all__'
        read_only_fields = ('created_at',)
    
    def get_target_name(self, obj):
        if obj.lead:
            return obj.lead.name
        elif obj.customer:
            return obj.customer.name
        elif obj.partner:
            return obj.partner.name
        return None


class SupplierRatingSerializer(serializers.ModelSerializer):
    """Supplier Rating serializer"""
    supplier_name = serializers.CharField(source='supplier.partner.name', read_only=True)
    rated_by_name = serializers.CharField(source='rated_by.get_full_name', read_only=True)
    
    class Meta:
        model = SupplierRating
        fields = '__all__'
        read_only_fields = ('overall_rating', 'rating_date')


class CRMConfigurationSerializer(serializers.ModelSerializer):
    """CRM Configuration serializer"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = CRMConfiguration
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


# Summary/Dashboard Serializers
class LeadSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for lead summaries"""
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    
    class Meta:
        model = Lead
        fields = ['id', 'name', 'company_name', 'status', 'priority', 'estimated_value', 
                 'assigned_to_name', 'lead_score', 'created_at']


class OpportunitySummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for opportunity summaries"""
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    weighted_value = serializers.DecimalField(source='get_weighted_value', max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = Opportunity
        fields = ['id', 'name', 'customer_name', 'estimated_value', 'weighted_value', 
                 'stage', 'probability', 'expected_close_date']


class CommunicationSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for communication summaries"""
    related_entity_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CommunicationLog
        fields = ['id', 'type', 'subject', 'related_entity_name', 'status', 'timestamp']
    
    def get_related_entity_name(self, obj):
        entity = obj.get_related_entity()
        return entity.name if entity else None


class CampaignSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for campaign summaries"""
    
    class Meta:
        model = Campaign
        fields = ['id', 'name', 'campaign_type', 'status', 'start_date', 'end_date', 
                 'budget', 'leads_generated', 'conversions'] 