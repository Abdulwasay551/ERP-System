from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from .models import (Customer, Lead, Opportunity, CommunicationLog, Partner, 
                    Campaign, CampaignTarget, SupplierRating, CRMConfiguration)
from .forms import (CustomerForm, LeadForm, OpportunityForm, CommunicationLogForm, 
                   CampaignForm, SupplierRatingForm, PartnerForm)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from django.contrib import messages
from django.core.paginator import Paginator
from accounting.models import Account
from sales.models import Customer as SalesCustomer, Quotation, SalesOrder
from purchase.models import Supplier

# Create your views here.

@login_required
def crm_dashboard(request):
    """Enhanced CRM module dashboard with comprehensive metrics and integrations"""
    company = request.user.company
    
    # Basic CRM metrics
    total_customers = Customer.objects.filter(company=company).count()
    total_leads = Lead.objects.filter(company=company).count()
    total_opportunities = Opportunity.objects.filter(company=company).count()
    total_partners = Partner.objects.filter(company=company).count()
    
    # Lead metrics
    new_leads = Lead.objects.filter(company=company, status='new').count()
    qualified_leads = Lead.objects.filter(company=company, status='qualified').count()
    converted_leads = Lead.objects.filter(company=company, status='converted').count()
    
    # Opportunity metrics
    active_opportunities = Opportunity.objects.filter(
        company=company, 
        stage__in=['qualification', 'proposal', 'negotiation']
    ).count()
    won_opportunities = Opportunity.objects.filter(company=company, stage='won').count()
    total_opportunity_value = Opportunity.objects.filter(company=company).aggregate(
        total=Sum('estimated_value'))['total'] or 0
    
    # Recent activities
    recent_customers = Customer.objects.filter(company=company).order_by('-created_at')[:5]
    recent_leads = Lead.objects.filter(company=company).order_by('-created_at')[:5]
    recent_opportunities = Opportunity.objects.filter(company=company).order_by('-created_at')[:5]
    recent_communications = CommunicationLog.objects.filter(company=company).order_by('-timestamp')[:10]
    
    # Sales integration - get sales data from sales module
    from sales.models import SalesOrder, Quotation
    total_sales_orders = SalesOrder.objects.filter(company=company).count()
    pending_quotations = Quotation.objects.filter(company=company, status='draft').count()
    
    # Purchase integration - get supplier data
    from purchase.models import Supplier
    total_suppliers = Supplier.objects.filter(company=company).count()
    
    # Monthly statistics
    current_month = timezone.now().replace(day=1)
    new_customers_this_month = Customer.objects.filter(
        company=company, 
        created_at__gte=current_month
    ).count()
    new_leads_this_month = Lead.objects.filter(
        company=company, 
        created_at__gte=current_month
    ).count()
    
    # Campaign metrics
    total_campaigns = Campaign.objects.filter(company=company).count()
    active_campaigns = Campaign.objects.filter(company=company, status='active').count()
    
    # Communication metrics
    calls_this_week = CommunicationLog.objects.filter(
        company=company,
        type='call',
        timestamp__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    # Follow-up reminders
    pending_followups = CommunicationLog.objects.filter(
        company=company,
        follow_up_required=True,
        follow_up_date__lte=timezone.now().date()
    ).count()
    
    # Lead conversion rate
    if total_leads > 0:
        conversion_rate = (converted_leads / total_leads) * 100
    else:
        conversion_rate = 0
    
    # Pipeline value by stage
    pipeline_by_stage = Opportunity.objects.filter(company=company).values('stage').annotate(
        count=Count('id'),
        total_value=Sum('estimated_value')
    )
    
    context = {
        # Basic metrics
        'total_customers': total_customers,
        'total_leads': total_leads,
        'total_opportunities': total_opportunities,
        'total_partners': total_partners,
        'total_suppliers': total_suppliers,
        'total_campaigns': active_campaigns,
        
        # Lead metrics
        'new_leads': new_leads,
        'qualified_leads': qualified_leads,
        'converted_leads': converted_leads,
        'conversion_rate': round(conversion_rate, 1),
        
        # Opportunity metrics
        'active_opportunities': active_opportunities,
        'won_opportunities': won_opportunities,
        'total_opportunity_value': total_opportunity_value,
        'pipeline_by_stage': pipeline_by_stage,
        
        # Monthly stats
        'new_customers_this_month': new_customers_this_month,
        'new_leads_this_month': new_leads_this_month,
        
        # Activity metrics
        'calls_this_week': calls_this_week,
        'pending_followups': pending_followups,
        
        # Recent activities
        'recent_customers': recent_customers,
        'recent_leads': recent_leads,
        'recent_opportunities': recent_opportunities,
        'recent_communications': recent_communications,
        
        # Sales integration
        'total_sales_orders': total_sales_orders,
        'pending_quotations': pending_quotations,
    }
    return render(request, 'crm/dashboard.html', context)

class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = 'crm/customer_list.html'
    context_object_name = 'customers'

    def get_queryset(self):
        return Customer.objects.filter(company=self.request.user.company)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add companies for the dropdown in the modal
        context['companies'] = Account.objects.filter(company=self.request.user.company)
        return context

class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'crm/customer_form.html'
    success_url = reverse_lazy('customer_list')

    def form_valid(self, form):
        form.instance.company = self.request.user.company
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'crm/customer_form.html'
    success_url = reverse_lazy('customer_list')

    def get_queryset(self):
        return Customer.objects.filter(company=self.request.user.company)

class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    model = Customer
    template_name = 'crm/customer_confirm_delete.html'
    success_url = reverse_lazy('customer_list')

    def get_queryset(self):
        return Customer.objects.filter(company=self.request.user.company)

class CustomerDetailView(LoginRequiredMixin, DetailView):
    model = Customer
    template_name = 'crm/customer_detail.html'
    context_object_name = 'customer'

    def get_queryset(self):
        return Customer.objects.filter(company=self.request.user.company)

class CustomerPageView(LoginRequiredMixin, TemplateView):
    template_name = 'crm/customer_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        # Get all customers for the company
        customers = Customer.objects.filter(company=company).select_related('created_by', 'account').order_by('-created_at')
        
        # Calculate statistics
        total_customers = customers.count()
        
        # Recent customers (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        new_customers = customers.filter(created_at__gte=thirty_days_ago).count()
        
        # Customers with linked accounts
        linked_accounts = customers.exclude(account__isnull=True).count()
        
        # Average customers per month (last 6 months)
        six_months_ago = timezone.now() - timedelta(days=180)
        monthly_avg = customers.filter(created_at__gte=six_months_ago).count() / 6
        
        # Get Chart of Accounts for dropdown
        coa_accounts = Account.objects.filter(company=company, account_type='Receivable')
        
        context.update({
            'customers': customers,
            'total_customers': total_customers,
            'new_customers': new_customers,
            'linked_accounts': linked_accounts,
            'monthly_avg': round(monthly_avg, 1),
            'coa_accounts': coa_accounts,
        })
        return context

class LeadPageView(LoginRequiredMixin, TemplateView):
    template_name = 'crm/lead_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        # Get all leads for the company with related data
        leads = Lead.objects.filter(company=company).select_related(
            'assigned_to', 'converted_to_customer', 'created_by'
        ).order_by('-created_at')
        
        # Calculate statistics
        total_leads = leads.count()
        new_leads = leads.filter(status='new').count()
        qualified_leads = leads.filter(status='qualified').count()
        converted_leads = leads.filter(status='converted').count()
        
        # Lead conversion rate
        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
        
        # Lead sources breakdown
        source_breakdown = leads.values('source').annotate(count=Count('id')).order_by('-count')
        
        # Priority breakdown
        priority_breakdown = leads.values('priority').annotate(count=Count('id'))
        
        # Get users for assignment dropdown
        users = company.users.all()
        
        # Status and source choices for filters
        status_choices = Lead.LEAD_STATUS_CHOICES
        source_choices = Lead.LEAD_SOURCE_CHOICES
        priority_choices = Lead.PRIORITY_CHOICES
        
        context.update({
            'leads': leads,
            'total_leads': total_leads,
            'new_leads': new_leads,
            'qualified_leads': qualified_leads,
            'converted_leads': converted_leads,
            'conversion_rate': round(conversion_rate, 1),
            'source_breakdown': source_breakdown,
            'priority_breakdown': priority_breakdown,
            'users': users,
            'status_choices': status_choices,
            'source_choices': source_choices,
            'priority_choices': priority_choices,
        })
        return context

class OpportunityPageView(LoginRequiredMixin, TemplateView):
    template_name = 'crm/opportunity_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        # Get all opportunities for the company with related data
        opportunities = Opportunity.objects.filter(company=company).select_related(
            'customer', 'assigned_to', 'account', 'lead'
        ).order_by('-created_at')
        
        # Calculate statistics
        total_opportunities = opportunities.count()
        total_value = opportunities.aggregate(total_value=Sum('estimated_value'))['total_value'] or 0
        
        # Stage breakdown
        stage_breakdown = opportunities.values('stage').annotate(
            count=Count('id'),
            total_value=Sum('estimated_value')
        ).order_by('-total_value')
        
        # Active opportunities (not won/lost/cancelled)
        active_opportunities = opportunities.exclude(stage__in=['won', 'lost', 'cancelled']).count()
        won_opportunities = opportunities.filter(stage='won').count()
        
        # Weighted pipeline value
        weighted_value = sum([opp.get_weighted_value() for opp in opportunities])
        
        # Get customers, leads and users for dropdowns
        customers = Customer.objects.filter(company=company)
        leads = Lead.objects.filter(company=company, status__in=['new', 'qualified'])
        users = company.users.all()
        coa_accounts = Account.objects.filter(company=company, account_type='Revenue')
        
        # Choices for filters
        stage_choices = Opportunity.OPPORTUNITY_STAGE_CHOICES
        priority_choices = Opportunity.PRIORITY_CHOICES
        probability_choices = Opportunity.PROBABILITY_CHOICES
        
        context.update({
            'opportunities': opportunities,
            'total_opportunities': total_opportunities,
            'total_value': total_value,
            'weighted_value': weighted_value,
            'active_opportunities': active_opportunities,
            'won_opportunities': won_opportunities,
            'stage_breakdown': stage_breakdown,
            'customers': customers,
            'leads': leads,
            'users': users,
            'coa_accounts': coa_accounts,
            'stage_choices': stage_choices,
            'priority_choices': priority_choices,
            'probability_choices': probability_choices,
        })
        return context

class CommunicationLogPageView(LoginRequiredMixin, TemplateView):
    template_name = 'crm/communicationlog_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        # Get all communication logs for the company with related data
        communications = CommunicationLog.objects.filter(company=company).select_related(
            'customer', 'lead', 'partner', 'opportunity', 'user'
        ).order_by('-timestamp')
        
        # Calculate statistics
        total_communications = communications.count()
        calls_count = communications.filter(type='call').count()
        emails_count = communications.filter(type='email').count()
        meetings_count = communications.filter(type='meeting').count()
        
        # Follow-up statistics
        pending_followups = communications.filter(
            follow_up_required=True,
            follow_up_date__lte=timezone.now().date()
        ).count()
        
        # Communication type breakdown
        type_breakdown = communications.values('type').annotate(count=Count('id')).order_by('-count')
        
        # Get related objects for dropdowns
        customers = Customer.objects.filter(company=company)
        leads = Lead.objects.filter(company=company)
        partners = Partner.objects.filter(company=company)
        opportunities = Opportunity.objects.filter(company=company)
        users = company.users.all()
        
        # Choices for filters
        type_choices = CommunicationLog.COMMUNICATION_TYPE_CHOICES
        direction_choices = CommunicationLog.DIRECTION_CHOICES
        status_choices = CommunicationLog.STATUS_CHOICES
        
        context.update({
            'communications': communications,
            'total_communications': total_communications,
            'calls_count': calls_count,
            'emails_count': emails_count,
            'meetings_count': meetings_count,
            'pending_followups': pending_followups,
            'type_breakdown': type_breakdown,
            'customers': customers,
            'leads': leads,
            'partners': partners,
            'opportunities': opportunities,
            'users': users,
            'type_choices': type_choices,
            'direction_choices': direction_choices,
            'status_choices': status_choices,
        })
        return context

@login_required
def customers_ui(request):
    customers = Customer.objects.filter(company=request.user.company)
    return render(request, 'crm/customers-ui.html', {'customers': customers})


# === NEW ENHANCED VIEW CLASSES ===

class PartnerPageView(LoginRequiredMixin, TemplateView):
    template_name = 'crm/partner_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        # Get all partners for the company
        partners = Partner.objects.filter(company=company).select_related(
            'relationship_manager', 'created_by'
        ).order_by('-created_at')
        
        # Calculate statistics
        total_partners = partners.count()
        customers_count = partners.filter(is_customer=True).count()
        suppliers_count = partners.filter(is_supplier=True).count()
        employees_count = partners.filter(is_employee=True).count()
        leads_count = partners.filter(is_lead=True).count()
        
        # Partner type breakdown
        type_breakdown = partners.values('partner_type').annotate(count=Count('id'))
        
        # Active vs inactive
        active_partners = partners.filter(is_active=True).count()
        inactive_partners = total_partners - active_partners
        
        # Get users for relationship manager dropdown
        users = company.users.all()
        
        # Choices for filters
        partner_type_choices = Partner.PARTNER_TYPE_CHOICES
        payment_terms_choices = Partner.PAYMENT_TERMS_CHOICES
        currency_choices = Partner.CURRENCY_CHOICES
        
        context.update({
            'partners': partners,
            'total_partners': total_partners,
            'customers_count': customers_count,
            'suppliers_count': suppliers_count,
            'employees_count': employees_count,
            'leads_count': leads_count,
            'active_partners': active_partners,
            'inactive_partners': inactive_partners,
            'type_breakdown': type_breakdown,
            'users': users,
            'partner_type_choices': partner_type_choices,
            'payment_terms_choices': payment_terms_choices,
            'currency_choices': currency_choices,
        })
        return context


class CampaignPageView(LoginRequiredMixin, TemplateView):
    template_name = 'crm/campaign_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        # Get all campaigns for the company
        campaigns = Campaign.objects.filter(company=company).select_related(
            'campaign_manager', 'created_by'
        ).prefetch_related('team_members').order_by('-created_at')
        
        # Calculate statistics
        total_campaigns = campaigns.count()
        active_campaigns = campaigns.filter(status='active').count()
        completed_campaigns = campaigns.filter(status='completed').count()
        total_budget = campaigns.aggregate(total=Sum('budget'))['total'] or 0
        total_leads_generated = campaigns.aggregate(total=Sum('leads_generated'))['total'] or 0
        
        # Campaign type breakdown
        type_breakdown = campaigns.values('campaign_type').annotate(
            count=Count('id'),
            total_budget=Sum('budget'),
            total_leads=Sum('leads_generated')
        )
        
        # Status breakdown
        status_breakdown = campaigns.values('status').annotate(count=Count('id'))
        
        # Get users for team assignment
        users = company.users.all()
        
        # Choices for filters
        campaign_type_choices = Campaign.CAMPAIGN_TYPE_CHOICES
        status_choices = Campaign.STATUS_CHOICES
        
        context.update({
            'campaigns': campaigns,
            'total_campaigns': total_campaigns,
            'active_campaigns': active_campaigns,
            'completed_campaigns': completed_campaigns,
            'total_budget': total_budget,
            'total_leads_generated': total_leads_generated,
            'type_breakdown': type_breakdown,
            'status_breakdown': status_breakdown,
            'users': users,
            'campaign_type_choices': campaign_type_choices,
            'status_choices': status_choices,
        })
        return context


class SupplierIntegrationView(LoginRequiredMixin, TemplateView):
    """View to show CRM integration with Purchase module suppliers"""
    template_name = 'crm/supplier_integration.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        # Get suppliers from purchase module
        suppliers = Supplier.objects.filter(company=company).select_related(
            'partner', 'created_by'
        ).order_by('-created_at')
        
        # Get supplier ratings
        supplier_ratings = SupplierRating.objects.filter(company=company).select_related(
            'supplier', 'rated_by'
        ).order_by('-rating_date')
        
        # Statistics
        total_suppliers = suppliers.count()
        active_suppliers = suppliers.filter(status='active').count()
        avg_quality_rating = supplier_ratings.aggregate(avg=Avg('quality_rating'))['avg'] or 0
        avg_delivery_rating = supplier_ratings.aggregate(avg=Avg('delivery_rating'))['avg'] or 0
        
        # Supplier type breakdown
        type_breakdown = suppliers.values('supplier_type').annotate(count=Count('id'))
        
        # Top rated suppliers
        top_suppliers = suppliers.filter(overall_rating__gt=8).order_by('-overall_rating')[:5]
        
        context.update({
            'suppliers': suppliers,
            'supplier_ratings': supplier_ratings,
            'total_suppliers': total_suppliers,
            'active_suppliers': active_suppliers,
            'avg_quality_rating': round(avg_quality_rating, 1),
            'avg_delivery_rating': round(avg_delivery_rating, 1),
            'type_breakdown': type_breakdown,
            'top_suppliers': top_suppliers,
        })
        return context


class SalesIntegrationView(LoginRequiredMixin, TemplateView):
    """View to show CRM integration with Sales module"""
    template_name = 'crm/sales_integration.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        # Import sales models
        from sales.models import SalesOrder, Quotation, Invoice
        
        # Get sales data linked to CRM customers
        customers = Customer.objects.filter(company=company)
        sales_orders = SalesOrder.objects.filter(company=company, customer__in=customers)
        quotations = Quotation.objects.filter(company=company, customer__in=customers)
        
        # Statistics
        total_sales_value = sales_orders.aggregate(total=Sum('total'))['total'] or 0
        pending_quotations = quotations.filter(status='draft').count()
        active_orders = sales_orders.filter(status__in=['confirmed', 'in_progress']).count()
        
        # Customer sales ranking
        customer_sales = customers.annotate(
            total_sales=Sum('sales_orders__total')
        ).filter(total_sales__isnull=False).order_by('-total_sales')[:10]
        
        # Recent activities
        recent_orders = sales_orders.order_by('-created_at')[:10]
        recent_quotations = quotations.order_by('-created_at')[:10]
        
        context.update({
            'customers': customers,
            'sales_orders': sales_orders,
            'quotations': quotations,
            'total_sales_value': total_sales_value,
            'pending_quotations': pending_quotations,
            'active_orders': active_orders,
            'customer_sales': customer_sales,
            'recent_orders': recent_orders,
            'recent_quotations': recent_quotations,
        })
        return context

@login_required
@require_POST
def customers_add(request):
    name = request.POST.get('name')
    email = request.POST.get('email')
    phone = request.POST.get('phone', '')
    address = request.POST.get('address', '')
    account_id = request.POST.get('account_id')
    customer_type = request.POST.get('customer_type', 'individual')
    tax_id = request.POST.get('tax_id', '')
    notes = request.POST.get('notes', '')
    
    if not name or not email:
        return JsonResponse({'success': False, 'error': 'Name and email are required.'}, status=400)
    
    try:
        account = None
        if account_id:
            account = get_object_or_404(Account, pk=account_id, company=request.user.company)
        
        # Create customer with base fields
        customer_data = {
            'company': request.user.company,
            'name': name,
            'email': email,
            'phone': phone,
            'address': address,
            'account': account,
            'created_by': request.user
        }
        
        # Add additional fields if they exist in the model
        if hasattr(Customer, 'customer_type'):
            customer_data['customer_type'] = customer_type
        if hasattr(Customer, 'tax_id'):
            customer_data['tax_id'] = tax_id
        if hasattr(Customer, 'notes'):
            customer_data['notes'] = notes
            
        customer = Customer.objects.create(**customer_data)
        
        return JsonResponse({
            'success': True,
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'email': customer.email,
                'phone': customer.phone,
                'address': customer.address,
                'account': customer.account.name if customer.account else '',
                'created_at': customer.created_at.strftime('%Y-%m-%d')
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def customers_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk, company=request.user.company)
    
    if request.method == 'GET':
        return JsonResponse({
            'success': True,
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'email': customer.email,
                'phone': customer.phone,
                'address': customer.address,
                'company': customer.account.id if customer.account else '',
                'customer_type': getattr(customer, 'customer_type', 'individual'),
                'tax_id': getattr(customer, 'tax_id', ''),
                'notes': getattr(customer, 'notes', ''),
                'created_at': customer.created_at.strftime('%Y-%m-%d')
            }
        })
    
    elif request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        address = request.POST.get('address', '')
        account_id = request.POST.get('account_id')
        customer_type = request.POST.get('customer_type', 'individual')
        tax_id = request.POST.get('tax_id', '')
        notes = request.POST.get('notes', '')
        
        if not name or not email:
            return JsonResponse({'success': False, 'error': 'Name and email are required.'}, status=400)
        
        try:
            account = None
            if account_id:
                account = get_object_or_404(Account, pk=account_id, company=request.user.company)
                
            customer.name = name
            customer.email = email
            customer.phone = phone
            customer.address = address
            customer.account = account
            
            # Update additional fields if they exist
            if hasattr(customer, 'customer_type'):
                customer.customer_type = customer_type
            if hasattr(customer, 'tax_id'):
                customer.tax_id = tax_id
            if hasattr(customer, 'notes'):
                customer.notes = notes
                
            customer.save()
            
            return JsonResponse({
                'success': True,
                'customer': {
                    'id': customer.id,
                    'name': customer.name,
                    'email': customer.email,
                    'phone': customer.phone,
                    'address': customer.address,
                    'account': customer.account.name if customer.account else '',
                    'created_at': customer.created_at.strftime('%Y-%m-%d')
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def customers_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk, company=request.user.company)
    try:
        customer.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# Lead CRUD Operations
@login_required
@require_POST
def leads_add(request):
    name = request.POST.get('name')
    email = request.POST.get('email', '')
    phone = request.POST.get('phone', '')
    source = request.POST.get('source', '')
    status = request.POST.get('status', 'New')
    assigned_to_id = request.POST.get('assigned_to_id')
    
    if not name:
        return JsonResponse({'success': False, 'error': 'Name is required.'}, status=400)
    
    try:
        assigned_to = None
        if assigned_to_id:
            assigned_to = get_object_or_404(request.user.company.users, pk=assigned_to_id)
            
        lead = Lead.objects.create(
            company=request.user.company,
            name=name,
            email=email,
            phone=phone,
            source=source,
            status=status,
            assigned_to=assigned_to
        )
        return JsonResponse({
            'success': True,
            'lead': {
                'id': lead.id,
                'name': lead.name,
                'email': lead.email,
                'phone': lead.phone,
                'source': lead.source,
                'status': lead.status,
                'assigned_to': lead.assigned_to.get_full_name() if lead.assigned_to else '',
                'created_at': lead.created_at.strftime('%Y-%m-%d')
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def leads_edit(request, pk):
    lead = get_object_or_404(Lead, pk=pk, company=request.user.company)
    name = request.POST.get('name')
    email = request.POST.get('email', '')
    phone = request.POST.get('phone', '')
    source = request.POST.get('source', '')
    status = request.POST.get('status')
    assigned_to_id = request.POST.get('assigned_to_id')
    
    if not name:
        return JsonResponse({'success': False, 'error': 'Name is required.'}, status=400)
    
    try:
        assigned_to = None
        if assigned_to_id:
            assigned_to = get_object_or_404(request.user.company.users, pk=assigned_to_id)
            
        lead.name = name
        lead.email = email
        lead.phone = phone
        lead.source = source
        lead.status = status if status else lead.status
        lead.assigned_to = assigned_to
        lead.save()
        
        return JsonResponse({
            'success': True,
            'lead': {
                'id': lead.id,
                'name': lead.name,
                'email': lead.email,
                'phone': lead.phone,
                'source': lead.source,
                'status': lead.status,
                'assigned_to': lead.assigned_to.get_full_name() if lead.assigned_to else '',
                'created_at': lead.created_at.strftime('%Y-%m-%d')
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def leads_delete(request, pk):
    lead = get_object_or_404(Lead, pk=pk, company=request.user.company)
    try:
        lead.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# Opportunity CRUD Operations
@login_required
@require_POST
def opportunities_add(request):
    name = request.POST.get('name')
    customer_id = request.POST.get('customer_id')
    value = request.POST.get('value')
    stage = request.POST.get('stage', 'Qualification')
    close_date = request.POST.get('close_date')
    assigned_to_id = request.POST.get('assigned_to_id')
    account_id = request.POST.get('account_id')
    
    if not name or not customer_id or not value:
        return JsonResponse({'success': False, 'error': 'Name, customer, and value are required.'}, status=400)
    
    try:
        customer = get_object_or_404(Customer, pk=customer_id, company=request.user.company)
        assigned_to = None
        if assigned_to_id:
            assigned_to = get_object_or_404(request.user.company.users, pk=assigned_to_id)
        account = None
        if account_id:
            account = get_object_or_404(Account, pk=account_id, company=request.user.company)
            
        opportunity = Opportunity.objects.create(
            company=request.user.company,
            name=name,
            customer=customer,
            value=Decimal(value),
            stage=stage,
            close_date=close_date if close_date else None,
            assigned_to=assigned_to,
            account=account
        )
        return JsonResponse({
            'success': True,
            'opportunity': {
                'id': opportunity.id,
                'name': opportunity.name,
                'customer_name': opportunity.customer.name,
                'value': str(opportunity.value),
                'stage': opportunity.stage,
                'close_date': opportunity.close_date.strftime('%Y-%m-%d') if opportunity.close_date else '',
                'assigned_to': opportunity.assigned_to.get_full_name() if opportunity.assigned_to else '',
                'account': opportunity.account.name if opportunity.account else '',
                'created_at': opportunity.created_at.strftime('%Y-%m-%d')
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def opportunities_edit(request, pk):
    opportunity = get_object_or_404(Opportunity, pk=pk, company=request.user.company)
    name = request.POST.get('name')
    customer_id = request.POST.get('customer_id')
    value = request.POST.get('value')
    stage = request.POST.get('stage')
    close_date = request.POST.get('close_date')
    assigned_to_id = request.POST.get('assigned_to_id')
    account_id = request.POST.get('account_id')
    
    if not name or not customer_id or not value:
        return JsonResponse({'success': False, 'error': 'Name, customer, and value are required.'}, status=400)
    
    try:
        customer = get_object_or_404(Customer, pk=customer_id, company=request.user.company)
        assigned_to = None
        if assigned_to_id:
            assigned_to = get_object_or_404(request.user.company.users, pk=assigned_to_id)
        account = None
        if account_id:
            account = get_object_or_404(Account, pk=account_id, company=request.user.company)
            
        opportunity.name = name
        opportunity.customer = customer
        opportunity.value = Decimal(value)
        opportunity.stage = stage if stage else opportunity.stage
        opportunity.close_date = close_date if close_date else None
        opportunity.assigned_to = assigned_to
        opportunity.account = account
        opportunity.save()
        
        return JsonResponse({
            'success': True,
            'opportunity': {
                'id': opportunity.id,
                'name': opportunity.name,
                'customer_name': opportunity.customer.name,
                'value': str(opportunity.value),
                'stage': opportunity.stage,
                'close_date': opportunity.close_date.strftime('%Y-%m-%d') if opportunity.close_date else '',
                'assigned_to': opportunity.assigned_to.get_full_name() if opportunity.assigned_to else '',
                'account': opportunity.account.name if opportunity.account else '',
                'created_at': opportunity.created_at.strftime('%Y-%m-%d')
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def opportunities_delete(request, pk):
    opportunity = get_object_or_404(Opportunity, pk=pk, company=request.user.company)
    try:
        opportunity.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# Communication Log CRUD Operations
@login_required
@require_POST
def communications_add(request):
    customer_id = request.POST.get('customer_id')
    type = request.POST.get('type', 'call')
    subject = request.POST.get('subject', '')
    notes = request.POST.get('notes', '')
    
    if not customer_id:
        return JsonResponse({'success': False, 'error': 'Customer is required.'}, status=400)
    
    try:
        customer = get_object_or_404(Customer, pk=customer_id, company=request.user.company)
        
        communication = CommunicationLog.objects.create(
            company=request.user.company,
            customer=customer,
            user=request.user,
            type=type,
            subject=subject,
            notes=notes
        )
        return JsonResponse({
            'success': True,
            'communication': {
                'id': communication.id,
                'customer_name': communication.customer.name,
                'user_name': communication.user.get_full_name() if communication.user else '',
                'type': communication.type,
                'subject': communication.subject,
                'notes': communication.notes,
                'timestamp': communication.timestamp.strftime('%Y-%m-%d %H:%M')
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def communications_edit(request, pk):
    communication = get_object_or_404(CommunicationLog, pk=pk, company=request.user.company)
    customer_id = request.POST.get('customer_id')
    type = request.POST.get('type')
    subject = request.POST.get('subject', '')
    notes = request.POST.get('notes', '')
    
    if not customer_id:
        return JsonResponse({'success': False, 'error': 'Customer is required.'}, status=400)
    
    try:
        customer = get_object_or_404(Customer, pk=customer_id, company=request.user.company)
        
        communication.customer = customer
        communication.type = type if type else communication.type
        communication.subject = subject
        communication.notes = notes
        communication.save()
        
        return JsonResponse({
            'success': True,
            'communication': {
                'id': communication.id,
                'customer_name': communication.customer.name,
                'user_name': communication.user.get_full_name() if communication.user else '',
                'type': communication.type,
                'subject': communication.subject,
                'notes': communication.notes,
                'timestamp': communication.timestamp.strftime('%Y-%m-%d %H:%M')
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def communications_delete(request, pk):
    communication = get_object_or_404(CommunicationLog, pk=pk, company=request.user.company)
    try:
        communication.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# Enhanced List Views for CRM Templates

class LeadListView(LoginRequiredMixin, ListView):
    model = Lead
    template_name = 'crm/lead_list.html'
    context_object_name = 'leads'
    paginate_by = 20

    def get_queryset(self):
        queryset = Lead.objects.filter(company=self.request.user.company).order_by('-created_at')
        
        # Apply filters
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(email__icontains=search) | 
                Q(company_name__icontains=search)
            )
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        source = self.request.GET.get('source')
        if source:
            queryset = queryset.filter(source=source)
        
        assigned_to = self.request.GET.get('assigned_to')
        if assigned_to:
            queryset = queryset.filter(assigned_to_id=assigned_to)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        # Statistics
        context['total_leads'] = Lead.objects.filter(company=company).count()
        context['new_leads'] = Lead.objects.filter(company=company, status='new').count()
        context['qualified_leads'] = Lead.objects.filter(company=company, status='qualified').count()
        context['converted_leads'] = Lead.objects.filter(company=company, status='converted').count()
        context['avg_lead_score'] = Lead.objects.filter(company=company).aggregate(
            avg_score=Avg('lead_score'))['avg_score'] or 0
        
        # Filter choices
        context['status_choices'] = Lead.LEAD_STATUS_CHOICES
        context['source_choices'] = Lead.LEAD_SOURCE_CHOICES
        
        return context


class OpportunityListView(LoginRequiredMixin, ListView):
    model = Opportunity
    template_name = 'crm/opportunity_list.html'
    context_object_name = 'opportunities'
    paginate_by = 20

    def get_queryset(self):
        queryset = Opportunity.objects.filter(company=self.request.user.company).order_by('-created_at')
        
        # Apply filters
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(Q(name__icontains=search))
        
        stage = self.request.GET.get('stage')
        if stage:
            queryset = queryset.filter(stage=stage)
        
        probability_min = self.request.GET.get('probability_min')
        if probability_min:
            queryset = queryset.filter(probability__gte=probability_min)
        
        assigned_to = self.request.GET.get('assigned_to')
        if assigned_to:
            queryset = queryset.filter(assigned_to_id=assigned_to)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        # Statistics
        context['total_opportunities'] = Opportunity.objects.filter(company=company).count()
        context['open_opportunities'] = Opportunity.objects.filter(
            company=company, stage__in=['qualification', 'proposal', 'negotiation']).count()
        context['won_opportunities'] = Opportunity.objects.filter(company=company, stage='won').count()
        context['total_value'] = Opportunity.objects.filter(company=company).aggregate(
            total=Sum('estimated_value'))['total'] or 0
        context['avg_probability'] = Opportunity.objects.filter(company=company).aggregate(
            avg_prob=Avg('probability'))['avg_prob'] or 0
        
        # Filter choices
        context['stage_choices'] = Opportunity.OPPORTUNITY_STAGE_CHOICES
        
        return context


class CommunicationLogListView(LoginRequiredMixin, ListView):
    model = CommunicationLog
    template_name = 'crm/communicationlog_list.html'
    context_object_name = 'communications'
    paginate_by = 20

    def get_queryset(self):
        queryset = CommunicationLog.objects.filter(company=self.request.user.company).order_by('-timestamp')
        
        # Apply filters
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(Q(subject__icontains=search) | Q(notes__icontains=search))
        
        communication_type = self.request.GET.get('type')
        if communication_type:
            queryset = queryset.filter(type=communication_type)
        
        direction = self.request.GET.get('direction')
        if direction:
            queryset = queryset.filter(direction=direction)
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        # Statistics
        context['total_communications'] = CommunicationLog.objects.filter(company=company).count()
        context['pending_communications'] = CommunicationLog.objects.filter(
            company=company, status='pending').count()
        context['completed_communications'] = CommunicationLog.objects.filter(
            company=company, status='completed').count()
        context['today_communications'] = CommunicationLog.objects.filter(
            company=company, timestamp__date=timezone.now().date()).count()
        context['follow_ups_needed'] = CommunicationLog.objects.filter(
            company=company, follow_up_required=True, status='pending').count()
        
        # Filter choices
        context['type_choices'] = CommunicationLog.COMMUNICATION_TYPE_CHOICES
        context['direction_choices'] = CommunicationLog.DIRECTION_CHOICES
        context['status_choices'] = CommunicationLog.STATUS_CHOICES
        
        return context


class PartnerListView(LoginRequiredMixin, ListView):
    model = Partner
    template_name = 'crm/partner_list.html'
    context_object_name = 'partners'
    paginate_by = 20

    def get_queryset(self):
        queryset = Partner.objects.filter(company=self.request.user.company).order_by('-created_at')
        
        # Apply filters
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(email__icontains=search))
        
        partner_type = self.request.GET.get('partner_type')
        if partner_type:
            queryset = queryset.filter(partner_type=partner_type)
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        industry = self.request.GET.get('industry')
        if industry:
            queryset = queryset.filter(industry=industry)
        
        country = self.request.GET.get('country')
        if country:
            queryset = queryset.filter(country=country)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        # Statistics
        context['total_partners'] = Partner.objects.filter(company=company).count()
        context['active_partners'] = Partner.objects.filter(company=company, status='active').count()
        context['suppliers_count'] = Partner.objects.filter(
            company=company, partner_type='supplier').count()
        context['vendors_count'] = Partner.objects.filter(
            company=company, partner_type='vendor').count()
        context['avg_rating'] = Partner.objects.filter(company=company).aggregate(
            avg_rating=Avg('rating'))['avg_rating'] or 0
        
        # Filter choices
        context['type_choices'] = Partner.PARTNER_TYPE_CHOICES
        context['payment_terms_choices'] = Partner.PAYMENT_TERMS_CHOICES
        context['currency_choices'] = Partner.CURRENCY_CHOICES
        context['industries'] = Partner.objects.filter(company=company).values_list(
            'industry', flat=True).distinct()
        context['countries'] = Partner.objects.filter(company=company).values_list(
            'country', flat=True).distinct()
        
        return context


class CampaignListView(LoginRequiredMixin, ListView):
    model = Campaign
    template_name = 'crm/campaign_list.html'
    context_object_name = 'campaigns'
    paginate_by = 20

    def get_queryset(self):
        queryset = Campaign.objects.filter(company=self.request.user.company).order_by('-created_at')
        
        # Apply filters
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(description__icontains=search))
        
        campaign_type = self.request.GET.get('campaign_type')
        if campaign_type:
            queryset = queryset.filter(campaign_type=campaign_type)
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        channel = self.request.GET.get('channel')
        if channel:
            queryset = queryset.filter(channel=channel)
        
        date_range = self.request.GET.get('date_range')
        if date_range == 'active':
            today = timezone.now().date()
            queryset = queryset.filter(
                start_date__lte=today,
                end_date__gte=today,
                status='active'
            )
        elif date_range == 'this_month':
            today = timezone.now().date()
            queryset = queryset.filter(start_date__month=today.month, start_date__year=today.year)
        elif date_range == 'last_month':
            last_month = timezone.now().date().replace(day=1) - timedelta(days=1)
            queryset = queryset.filter(start_date__month=last_month.month, start_date__year=last_month.year)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        # Statistics
        context['total_campaigns'] = Campaign.objects.filter(company=company).count()
        context['active_campaigns'] = Campaign.objects.filter(company=company, status='active').count()
        context['total_reach'] = Campaign.objects.filter(company=company).aggregate(
            total=Sum('impressions'))['total'] or 0
        context['total_budget'] = Campaign.objects.filter(company=company).aggregate(
            total=Sum('budget'))['total'] or 0
        # Calculate ROI based on revenue_generated / actual_cost
        campaigns_with_roi = Campaign.objects.filter(company=company, actual_cost__gt=0)
        if campaigns_with_roi.exists():
            total_revenue = campaigns_with_roi.aggregate(total=Sum('revenue_generated'))['total'] or 0
            total_cost = campaigns_with_roi.aggregate(total=Sum('actual_cost'))['total'] or 0
            context['avg_roi'] = (total_revenue / total_cost * 100) if total_cost > 0 else 0
        else:
            context['avg_roi'] = 0
        
        # Filter choices
        context['type_choices'] = Campaign.CAMPAIGN_TYPE_CHOICES
        context['status_choices'] = Campaign.STATUS_CHOICES
        context['channels'] = Campaign.objects.filter(company=company).values_list(
            'channel', flat=True).distinct()
        
        return context


# === FORM-BASED CRUD VIEWS ===

class LeadCreateView(LoginRequiredMixin, CreateView):
    model = Lead
    form_class = LeadForm
    template_name = 'crm/lead_form.html'
    success_url = '/crm/leads/'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs
    
    def form_valid(self, form):
        form.instance.company = self.request.user.company
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class LeadUpdateView(LoginRequiredMixin, UpdateView):
    model = Lead
    form_class = LeadForm
    template_name = 'crm/lead_form.html'
    success_url = '/crm/leads/'
    
    def get_queryset(self):
        return Lead.objects.filter(company=self.request.user.company)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs


class LeadDetailView(LoginRequiredMixin, DetailView):
    model = Lead
    template_name = 'crm/lead_detail.html'
    context_object_name = 'lead'
    
    def get_queryset(self):
        return Lead.objects.filter(company=self.request.user.company)


class LeadDeleteView(LoginRequiredMixin, DeleteView):
    model = Lead
    template_name = 'crm/lead_confirm_delete.html'
    success_url = '/crm/leads/'
    
    def get_queryset(self):
        return Lead.objects.filter(company=self.request.user.company)


class OpportunityCreateView(LoginRequiredMixin, CreateView):
    model = Opportunity
    form_class = OpportunityForm
    template_name = 'crm/opportunity_form.html'
    success_url = '/crm/opportunities/'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs
    
    def form_valid(self, form):
        form.instance.company = self.request.user.company
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class OpportunityUpdateView(LoginRequiredMixin, UpdateView):
    model = Opportunity
    form_class = OpportunityForm
    template_name = 'crm/opportunity_form.html'
    success_url = '/crm/opportunities/'
    
    def get_queryset(self):
        return Opportunity.objects.filter(company=self.request.user.company)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.user.company
        return kwargs


class OpportunityDetailView(LoginRequiredMixin, DetailView):
    model = Opportunity
    template_name = 'crm/opportunity_detail.html'
    context_object_name = 'opportunity'
    
    def get_queryset(self):
        return Opportunity.objects.filter(company=self.request.user.company)


class OpportunityDeleteView(LoginRequiredMixin, DeleteView):
    model = Opportunity
    template_name = 'crm/opportunity_confirm_delete.html'
    success_url = '/crm/opportunities/'
    
    def get_queryset(self):
        return Opportunity.objects.filter(company=self.request.user.company)