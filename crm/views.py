from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from .models import Customer
from .forms import CustomerForm
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Customer
from django.views.decorators.http import require_POST

# Create your views here.

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

class LeadPageView(LoginRequiredMixin, TemplateView):
    template_name = 'crm/lead_list.html'

class OpportunityPageView(LoginRequiredMixin, TemplateView):
    template_name = 'crm/opportunity_list.html'

class CommunicationLogPageView(LoginRequiredMixin, TemplateView):
    template_name = 'crm/communicationlog_list.html'

@login_required
def customers_ui(request):
    customers = Customer.objects.filter(company=request.user.company)
    return render(request, 'crm/customers-ui.html', {'customers': customers})

@login_required
@require_POST
def customers_add(request):
    name = request.POST.get('name')
    email = request.POST.get('email')
    phone = request.POST.get('phone')
    if not name or not email:
        return JsonResponse({'success': False, 'error': 'Name and email are required.'}, status=400)
    customer = Customer.objects.create(
        company=request.user.company,
        name=name,
        email=email,
        phone=phone or '',
        created_by=request.user
    )
    return JsonResponse({
        'success': True,
        'customer': {
            'id': customer.id,
            'name': customer.name,
            'email': customer.email,
            'phone': customer.phone,
            'account': customer.account.name if customer.account else ''
        }
    })

@login_required
@require_POST
def customers_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk, company=request.user.company)
    name = request.POST.get('name')
    email = request.POST.get('email')
    phone = request.POST.get('phone')
    if not name or not email:
        return JsonResponse({'success': False, 'error': 'Name and email are required.'}, status=400)
    customer.name = name
    customer.email = email
    customer.phone = phone or ''
    customer.save()
    return JsonResponse({
        'success': True,
        'customer': {
            'id': customer.id,
            'name': customer.name,
            'email': customer.email,
            'phone': customer.phone,
            'account': customer.account.name if customer.account else ''
        }
    })

@login_required
@require_POST
def customers_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk, company=request.user.company)
    customer.delete()
    return JsonResponse({'success': True})
