from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from .models import Customer
from .forms import CustomerForm

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
