from django.urls import path
from . import views
from .views import (
    crm_dashboard, CustomerPageView, LeadPageView, OpportunityPageView, CommunicationLogPageView,
    customers_ui, customers_add, customers_edit, customers_delete,
    leads_add, leads_edit, leads_delete,
    opportunities_add, opportunities_edit, opportunities_delete,
    communications_add, communications_edit, communications_delete
)

urlpatterns = [
    # Dashboard
    path('dashboard/', crm_dashboard, name='crm_dashboard'),
    path('dashboard-ui/', crm_dashboard, name='crm_dashboard_ui'),
    
    # Legacy Customer URLs (keeping for compatibility)
    path('customers/', views.CustomerListView.as_view(), name='customer_list'),
    path('customers/add/', views.CustomerCreateView.as_view(), name='customer_add'),
    path('customers/<int:pk>/', views.CustomerDetailView.as_view(), name='customer_detail'),
    path('customers/<int:pk>/edit/', views.CustomerUpdateView.as_view(), name='customer_edit'),
    path('customers/<int:pk>/delete/', views.CustomerDeleteView.as_view(), name='customer_delete'),
    
    # Modern template views with enhanced context data
    path('customers-ui/', CustomerPageView.as_view(), name='customer_page'),
    path('leads-ui/', LeadPageView.as_view(), name='lead_page'),
    path('opportunities-ui/', OpportunityPageView.as_view(), name='opportunity_page'),
    path('communications-ui/', CommunicationLogPageView.as_view(), name='communicationlog_page'),
    
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