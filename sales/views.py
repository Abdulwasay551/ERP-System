from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

# Create your views here.

class ProductPageView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/product_list.html'

class TaxPageView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/tax_list.html'

class QuotationPageView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/quotation_list.html'

class SalesOrderPageView(LoginRequiredMixin, TemplateView):
    template_name = 'sales/salesorder_list.html'
