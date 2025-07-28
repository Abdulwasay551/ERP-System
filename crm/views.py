from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from .models import Customer, Lead, Opportunity, CommunicationLog
from .forms import CustomerForm
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from accounting.models import Account

# Create your views here.

@login_required
def crm_dashboard(request):
    """CRM module dashboard with key metrics and quick access"""
    company = request.user.company
    
    # Key metrics
    total_customers = Customer.objects.filter(company=company).count()
    total_leads = Lead.objects.filter(company=company).count()
    total_opportunities = Opportunity.objects.filter(company=company).count()
    active_opportunities = Opportunity.objects.filter(company=company, stage__in=['prospecting', 'qualification', 'proposal']).count()
    
    # Monthly statistics
    current_month = timezone.now().replace(day=1)
    new_customers_this_month = Customer.objects.filter(
        company=company, 
        created_at__gte=current_month
    ).count()
    
    # Recent activities
    recent_customers = Customer.objects.filter(company=company).order_by('-created_at')[:5]
    recent_leads = Lead.objects.filter(company=company).order_by('-created_at')[:5]
    recent_opportunities = Opportunity.objects.filter(company=company).order_by('-created_at')[:5]
    
    context = {
        'total_customers': total_customers,
        'total_leads': total_leads,
        'total_opportunities': total_opportunities,
        'active_opportunities': active_opportunities,
        'new_customers_this_month': new_customers_this_month,
        'recent_customers': recent_customers,
        'recent_leads': recent_leads,
        'recent_opportunities': recent_opportunities,
    }
    return render(request, 'crm/dashboard.html', context)

class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = 'crm/customer_list.html'
    context_object_name = 'customers'

    def get_queryset(self):
        return Customer.objects.filter(company=self.request.user.company)

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
        
        # Get all leads for the company
        leads = Lead.objects.filter(company=company).select_related('assigned_to').order_by('-created_at')
        
        # Calculate statistics
        total_leads = leads.count()
        new_leads = leads.filter(status='New').count()
        qualified_leads = leads.filter(status='Qualified').count()
        converted_leads = leads.filter(status='Converted').count()
        
        # Get users for assignment dropdown
        users = company.users.all()
        
        context.update({
            'leads': leads,
            'total_leads': total_leads,
            'new_leads': new_leads,
            'qualified_leads': qualified_leads,
            'converted_leads': converted_leads,
            'users': users,
        })
        return context

class OpportunityPageView(LoginRequiredMixin, TemplateView):
    template_name = 'crm/opportunity_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        # Get all opportunities for the company
        opportunities = Opportunity.objects.filter(company=company).select_related('customer', 'assigned_to', 'account').order_by('-created_at')
        
        # Calculate statistics
        total_opportunities = opportunities.count()
        total_value = opportunities.aggregate(total_value=Sum('value'))['total_value'] or 0
        
        # Stage breakdown
        qualification_count = opportunities.filter(stage='Qualification').count()
        proposal_count = opportunities.filter(stage='Proposal').count()
        closed_won_count = opportunities.filter(stage='Closed Won').count()
        
        # Get customers and users for dropdowns
        customers = Customer.objects.filter(company=company)
        users = company.users.all()
        coa_accounts = Account.objects.filter(company=company, account_type='Revenue')
        
        context.update({
            'opportunities': opportunities,
            'total_opportunities': total_opportunities,
            'total_value': total_value,
            'qualification_count': qualification_count,
            'proposal_count': proposal_count,
            'closed_won_count': closed_won_count,
            'customers': customers,
            'users': users,
            'coa_accounts': coa_accounts,
        })
        return context

class CommunicationLogPageView(LoginRequiredMixin, TemplateView):
    template_name = 'crm/communicationlog_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.user.company
        
        # Get all communication logs for the company
        communications = CommunicationLog.objects.filter(company=company).select_related('customer', 'user').order_by('-timestamp')
        
        # Calculate statistics
        total_communications = communications.count()
        calls_count = communications.filter(type='call').count()
        emails_count = communications.filter(type='email').count()
        meetings_count = communications.filter(type='meeting').count()
        
        # Get customers and users for dropdowns
        customers = Customer.objects.filter(company=company)
        users = company.users.all()
        
        context.update({
            'communications': communications,
            'total_communications': total_communications,
            'calls_count': calls_count,
            'emails_count': emails_count,
            'meetings_count': meetings_count,
            'customers': customers,
            'users': users,
        })
        return context

@login_required
def customers_ui(request):
    customers = Customer.objects.filter(company=request.user.company)
    return render(request, 'crm/customers-ui.html', {'customers': customers})

@login_required
@require_POST
def customers_add(request):
    name = request.POST.get('name')
    email = request.POST.get('email')
    phone = request.POST.get('phone', '')
    address = request.POST.get('address', '')
    account_id = request.POST.get('account_id')
    
    if not name or not email:
        return JsonResponse({'success': False, 'error': 'Name and email are required.'}, status=400)
    
    try:
        account = None
        if account_id:
            account = get_object_or_404(Account, pk=account_id, company=request.user.company)
            
        customer = Customer.objects.create(
            company=request.user.company,
            name=name,
            email=email,
            phone=phone,
            address=address,
            account=account,
            created_by=request.user
        )
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
def customers_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk, company=request.user.company)
    name = request.POST.get('name')
    email = request.POST.get('email')
    phone = request.POST.get('phone', '')
    address = request.POST.get('address', '')
    account_id = request.POST.get('account_id')
    
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
