from django.urls import path
from . import views
from .views import (
    crm_dashboard, CustomerPageView, LeadPageView, OpportunityPageView, CommunicationLogPageView,
    PartnerPageView, CampaignPageView, SupplierIntegrationView, SalesIntegrationView, reports_ui,
    customers_ui, customers_add, customers_edit, customers_delete,
    leads_add, leads_edit, leads_delete,
    opportunities_add, opportunities_edit, opportunities_delete,
    communications_add, communications_edit, communications_delete,
    LeadListView, OpportunityListView, CommunicationLogListView, PartnerListView, CampaignListView,
    LeadCreateView, LeadUpdateView, LeadDetailView, LeadDeleteView,
    OpportunityCreateView, OpportunityUpdateView, OpportunityDetailView, OpportunityDeleteView
)

app_name = 'crm'

urlpatterns = [
    # Dashboard
    path('dashboard/', crm_dashboard, name='dashboard'),
    path('dashboard-ui/', crm_dashboard, name='crm_dashboard_ui'),
    
    # Reports
    path('reports/', reports_ui, name='reports'),
    path('reports-ui/', reports_ui, name='reports_ui'),
    
    # Legacy Customer URLs (keeping for compatibility)
    path('customers/', views.CustomerListView.as_view(), name='customer_list'),
    path('customers/add/', views.CustomerCreateView.as_view(), name='customer_add'),
    path('customers/<int:pk>/', views.CustomerDetailView.as_view(), name='customer_detail'),
    path('customers/<int:pk>/edit/', views.CustomerUpdateView.as_view(), name='customer_edit'),
    path('customers/<int:pk>/delete/', views.CustomerDeleteView.as_view(), name='customer_delete'),
    
    # Modern List Views for Enhanced Templates
    path('leads/', LeadListView.as_view(), name='lead_list'),
    path('opportunities/', OpportunityListView.as_view(), name='opportunity_list'),
    path('communications/', CommunicationLogListView.as_view(), name='communicationlog_list'),
    path('partners/', PartnerListView.as_view(), name='partner_list'),
    path('campaigns/', CampaignListView.as_view(), name='campaign_list'),
    
    # Lead CRUD Views
    path('leads/add/', LeadCreateView.as_view(), name='lead_add'),
    path('leads/<int:pk>/', LeadDetailView.as_view(), name='lead_detail'),
    path('leads/<int:pk>/edit/', LeadUpdateView.as_view(), name='lead_edit'),
    path('leads/<int:pk>/delete/', LeadDeleteView.as_view(), name='lead_delete'),
    
    # Opportunity CRUD Views
    path('opportunities/add/', OpportunityCreateView.as_view(), name='opportunity_add'),
    path('opportunities/<int:pk>/', OpportunityDetailView.as_view(), name='opportunity_detail'),
    path('opportunities/<int:pk>/edit/', OpportunityUpdateView.as_view(), name='opportunity_edit'),
    path('opportunities/<int:pk>/delete/', OpportunityDeleteView.as_view(), name='opportunity_delete'),
    
    # Modern template views with enhanced context data
    path('customers-ui/', CustomerPageView.as_view(), name='customer_page'),
    path('leads-ui/', LeadPageView.as_view(), name='lead_page'),
    path('opportunities-ui/', OpportunityPageView.as_view(), name='opportunity_page'),
    path('communications-ui/', CommunicationLogPageView.as_view(), name='communicationlog_page'),
    
    # Integration Views
    path('partners-ui/', PartnerPageView.as_view(), name='partner_page'),
    path('campaigns-ui/', CampaignPageView.as_view(), name='campaign_page'),
    path('supplier-integration/', SupplierIntegrationView.as_view(), name='supplier_integration'),
    path('sales-integration/', SalesIntegrationView.as_view(), name='sales_integration'),
    
    # Customer CRUD API endpoints
    path('customers-add/', customers_add, name='crm_customers_add'),
    path('customers-edit/<int:pk>/', customers_edit, name='crm_customers_edit'),
    path('customers-delete/<int:pk>/', customers_delete, name='crm_customers_delete'),
    
    # Lead CRUD API endpoints
    path('leads-add/', leads_add, name='crm_leads_add'),
    path('leads-edit/<int:pk>/', leads_edit, name='crm_leads_edit'),
    path('leads-delete/<int:pk>/', leads_delete, name='crm_leads_delete'),
    
    # Opportunity CRUD API endpoints
    path('opportunities-add/', opportunities_add, name='crm_opportunities_add'),
    path('opportunities-edit/<int:pk>/', opportunities_edit, name='crm_opportunities_edit'),
    path('opportunities-delete/<int:pk>/', opportunities_delete, name='crm_opportunities_delete'),
    
    # Communication Log CRUD API endpoints
    path('communications-add/', communications_add, name='crm_communications_add'),
    path('communications-edit/<int:pk>/', communications_edit, name='crm_communications_edit'),
    path('communications-delete/<int:pk>/', communications_delete, name='crm_communications_delete'),
]