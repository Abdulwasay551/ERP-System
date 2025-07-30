from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q, Sum, F, Count, Avg
from django.db import models
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
import json
from decimal import Decimal
from django.db.models.functions import TruncMonth
from .models import (
    UnitOfMeasure, Supplier, TaxChargesTemplate, PurchaseRequisition, PurchaseRequisitionItem,
    RequestForQuotation, RFQItem, SupplierQuotation, SupplierQuotationItem,
    PurchaseOrder, PurchaseOrderItem, PurchaseOrderTaxCharge,
    GoodsReceiptNote, GRNItem, GRNItemTracking, QualityInspection, QualityInspectionResult,
    PurchaseReturn, PurchaseReturnItem, Bill, BillItem, BillItemTracking, PurchasePayment,
    PurchaseApproval, GRNInventoryLock, SupplierLedger, SupplierContact, SupplierProductCatalog
)
from crm.models import Partner

from .forms import (
    UnitOfMeasureForm, SupplierForm, PurchaseRequisitionForm, RequestForQuotationForm,
    SupplierQuotationForm, PurchaseOrderForm, GoodsReceiptNoteForm, GRNItemForm,
    GRNItemTrackingForm, QualityInspectionForm, QualityInspectionResultForm,
    BillForm, PurchasePaymentForm, SupplierLedgerFilterForm, PurchaseReturnForm, PurchaseReturnItemForm,
    GRNItemFormSet, GRNItemTrackingFormSet, QualityInspectionResultFormSet,
    PurchaseReturnItemFormSet, SupplierContactForm, SupplierProductCatalogForm
)
from products.models import Product
from inventory.models import Warehouse
from .quotation_utils import QuotationComparison, UOMConverter, QuotationValidator

# =====================================
# DASHBOARD & OVERVIEW VIEWS
# =====================================

@login_required
def purchase_dashboard(request):
    """Enhanced Purchase module dashboard with key metrics and quotation insights"""
    try:
        company = request.user.company
        
        # Key metrics
        total_suppliers = Supplier.objects.filter(company=company, is_active=True).count()
        pending_requisitions = PurchaseRequisition.objects.filter(company=company, status='pending_approval').count()
        pending_orders = PurchaseOrder.objects.filter(company=company, status__in=['draft', 'pending_approval']).count()
        pending_bills = Bill.objects.filter(company=company, status__in=['draft', 'submitted']).count()
        
        # Quotation metrics
        active_rfqs = RequestForQuotation.objects.filter(company=company, status='sent').count()
        pending_quotations = SupplierQuotation.objects.filter(company=company, status='submitted').count()
        
        # Recent activities
        recent_requisitions = PurchaseRequisition.objects.filter(company=company).order_by('-created_at')[:5]
        recent_orders = PurchaseOrder.objects.filter(company=company).order_by('-created_at')[:5]
        recent_bills = Bill.objects.filter(company=company).order_by('-created_at')[:5]
        recent_rfqs = RequestForQuotation.objects.filter(company=company).order_by('-created_at')[:5]
        
        # Monthly statistics
        current_month = timezone.now().replace(day=1)
        monthly_orders = PurchaseOrder.objects.filter(
            company=company, 
            created_at__gte=current_month
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        context = {
            'total_suppliers': total_suppliers,
            'pending_requisitions': pending_requisitions,
            'pending_orders': pending_orders,
            'pending_bills': pending_bills,
            'active_rfqs': active_rfqs,
            'pending_quotations': pending_quotations,
            'recent_requisitions': recent_requisitions,
            'recent_orders': recent_orders,
            'recent_bills': recent_bills,
            'recent_rfqs': recent_rfqs,
            'monthly_orders': monthly_orders,
        }
        return render(request, 'purchase/dashboard.html', context)
    except Exception as e:
        context = {
            'total_suppliers': 0,
            'pending_requisitions': 0,
            'pending_orders': 0,
            'pending_bills': 0,
            'active_rfqs': 0,
            'pending_quotations': 0,
            'recent_requisitions': [],
            'recent_orders': [],
            'recent_bills': [],
            'recent_rfqs': [],
            'monthly_orders': 0,
            'error': str(e)
        }
        return render(request, 'purchase/dashboard.html', context)

# =====================================
# SUPPLIER MANAGEMENT VIEWS
# =====================================

@login_required
def suppliers_ui(request):
    """Enhanced supplier management interface with Partner model integration"""
    suppliers = Supplier.objects.filter(company=request.user.company).select_related('partner').order_by('partner__name')
    
    # Advanced filtering
    status_filter = request.GET.get('status', '')
    if status_filter:
        suppliers = suppliers.filter(status=status_filter)
    
    supplier_type_filter = request.GET.get('supplier_type', '')
    if supplier_type_filter:
        suppliers = suppliers.filter(supplier_type=supplier_type_filter)
    
    payment_terms_filter = request.GET.get('payment_terms', '')
    if payment_terms_filter:
        suppliers = suppliers.filter(partner__payment_terms=payment_terms_filter)
    
    # Rating filter
    min_rating = request.GET.get('min_rating', '')
    if min_rating:
        try:
            suppliers = suppliers.filter(overall_rating__gte=float(min_rating))
        except ValueError:
            pass
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        suppliers = suppliers.filter(
            Q(partner__name__icontains=search_query) |
            Q(supplier_code__icontains=search_query) |
            Q(partner__email__icontains=search_query) |
            Q(partner__phone__icontains=search_query) |
            Q(partner__contact_person__icontains=search_query) |
            Q(partner__city__icontains=search_query) |
            Q(partner__country__icontains=search_query)
        )
    
    # Get unique countries for filter dropdown
    countries = Supplier.objects.filter(company=request.user.company).select_related('partner').values_list('partner__country', flat=True).distinct().exclude(partner__country__isnull=True)
    
    # Calculate summary statistics
    total_suppliers = suppliers.count()
    active_suppliers = suppliers.filter(status='active').count()
    
    # TODO: Calculate these from actual transaction data
    total_payables = 0  # Sum of all outstanding payables
    pending_orders = 0  # Count of pending purchase orders
    avg_rating = suppliers.filter(overall_rating__gt=0).aggregate(avg=models.Avg('overall_rating'))['avg']
    
    # Pagination
    paginator = Paginator(suppliers, 25)
    page_number = request.GET.get('page')
    suppliers = paginator.get_page(page_number)
    
    context = {
        'suppliers': suppliers,
        'search_query': search_query,
        'status_filter': status_filter,
        'supplier_type_filter': supplier_type_filter,
        'payment_terms_filter': payment_terms_filter,
        'min_rating': min_rating,
        'total_suppliers': total_suppliers,
        'active_suppliers': active_suppliers,
        'avg_rating': round(avg_rating, 2) if avg_rating else 0,
        'supplier_statuses': Supplier.SUPPLIER_STATUS_CHOICES,
        'supplier_types': Supplier.SUPPLIER_TYPE_CHOICES,
        'payment_terms_choices': Partner.PAYMENT_TERMS_CHOICES,
        # Additional context for new template
        'countries': countries,
        'total_payables': total_payables,
        'pending_orders': pending_orders,
        'is_paginated': suppliers.has_other_pages(),
        'page_obj': suppliers,
    }
    
    return render(request, 'purchase/suppliers-ui.html', context)

@login_required
@login_required
def supplier_add(request):
    """Enhanced supplier creation with Partner model integration"""
    if request.method == 'POST':
        form = SupplierForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            try:
                supplier = form.save(commit=False)
                supplier.company = request.user.company
                supplier.created_by = request.user
                supplier.save()
                
                # Get the partner name from the form since supplier.name is now supplier.partner.name
                partner_name = form.cleaned_data.get('partner_name', 'Unknown')
                messages.success(request, f'Supplier {partner_name} (ID: {supplier.id}) created successfully.')
                return redirect('purchase:supplier_detail', pk=supplier.id)
                
            except Exception as e:
                messages.error(request, f'Error creating supplier: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = SupplierForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Add New Supplier',
        'supplier_types': Supplier.SUPPLIER_TYPE_CHOICES,
        'payment_terms': Partner.PAYMENT_TERMS_CHOICES,
        'currencies': Partner.CURRENCY_CHOICES,
    }
    return render(request, 'purchase/supplier-form.html', context)

@login_required
def supplier_edit(request, pk):
    """Enhanced supplier editing with Partner model integration"""
    supplier = get_object_or_404(Supplier, pk=pk, company=request.user.company)
    
    if request.method == 'POST':
        form = SupplierForm(request.POST, request.FILES, instance=supplier, user=request.user)
        if form.is_valid():
            try:
                supplier = form.save()
                partner_name = supplier.partner.name if supplier.partner else 'Unknown'
                messages.success(request, f'Supplier {partner_name} updated successfully.')
                return redirect('purchase:supplier_detail', pk=supplier.id)
                
            except Exception as e:
                messages.error(request, f'Error updating supplier: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = SupplierForm(instance=supplier, user=request.user)
    
    context = {
        'form': form,
        'supplier': supplier,
        'title': f'Edit Supplier - {supplier.partner.name if supplier.partner else "Unknown"}',
        'supplier_types': Supplier.SUPPLIER_TYPE_CHOICES,
        'payment_terms': Partner.PAYMENT_TERMS_CHOICES,
        'currencies': Partner.CURRENCY_CHOICES,
    }
    return render(request, 'purchase/supplier-form.html', context)

@login_required
def supplier_detail(request, pk):
    """Enhanced supplier detail view with Partner model integration"""
    supplier = get_object_or_404(Supplier, pk=pk, company=request.user.company)
    
    # Get related data
    contacts = supplier.contacts.filter(is_active=True).order_by('contact_type', 'name')
    recent_orders = supplier.purchase_orders.order_by('-created_at')[:10]
    recent_bills = supplier.bills.order_by('-created_at')[:10]
    recent_payments = supplier.payments.order_by('-created_at')[:10]
    
    # Calculate financial summary
    total_orders = supplier.purchase_orders.aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    total_bills = supplier.bills.filter(
        status__in=['approved', 'paid']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    total_payments = supplier.payments.filter(
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    outstanding_balance = total_bills - total_payments
    
    # Get partner information
    partner = supplier.partner if supplier.partner else None
    
    context = {
        'supplier': supplier,
        'partner': partner,
        'contacts': contacts,
        'recent_orders': recent_orders,
        'recent_bills': recent_bills,
        'recent_payments': recent_payments,
        'total_orders': total_orders,
        'total_bills': total_bills,
        'total_payments': total_payments,
        'outstanding_balance': outstanding_balance,
        'title': f'Supplier Details - {partner.name if partner else "Unknown"}',
        'page_title': 'Supplier Details',
        # Additional context for templates
        'supplier_contacts': contacts,
        'recent_activities': recent_orders[:5],  # Use recent orders as activities
        'total_amount': total_orders,
        'avg_delivery_time': supplier.delivery_lead_time if supplier.delivery_lead_time else "N/A",
    }
    return render(request, 'purchase/supplier-detail.html', context)


@login_required 
def supplier_contacts(request, supplier_id):
    """Manage supplier contacts"""
    supplier = get_object_or_404(Supplier, id=supplier_id, company=request.user.company)
    contacts = supplier.contacts.all().order_by('contact_type', 'name')
    
    if request.method == 'POST':
        form = SupplierContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.supplier = supplier
            contact.save()
            
            messages.success(request, f'Contact {contact.name} added successfully.')
            return redirect('purchase:supplier_contacts', supplier_id=supplier.id)
    else:
        form = SupplierContactForm()
    
    context = {
        'supplier': supplier,
        'contacts': contacts,
        'form': form,
        'title': f'Manage Contacts - {supplier.name}'
    }
    return render(request, 'purchase/supplier-contacts.html', context)

@login_required
def supplier_catalog(request, supplier_id):
    """Manage supplier product catalog"""
    supplier = get_object_or_404(Supplier, id=supplier_id, company=request.user.company)
    catalog_items = supplier.product_catalog.all().order_by('product__name')
    
    if request.method == 'POST':
        form = SupplierProductCatalogForm(request.POST, user=request.user)
        if form.is_valid():
            catalog_item = form.save(commit=False)
            catalog_item.supplier = supplier
            catalog_item.save()
            
            messages.success(request, f'Product {catalog_item.product.name} added to catalog.')
            return redirect('purchase:supplier_catalog', supplier_id=supplier.id)
    else:
        form = SupplierProductCatalogForm(user=request.user)
    
    context = {
        'supplier': supplier,
        'catalog_items': catalog_items,
        'form': form,
        'title': f'Product Catalog - {supplier.name}'
    }
    return render(request, 'purchase/supplier-catalog.html', context)

# =====================================
# PURCHASE REQUISITION VIEWS
# =====================================

@login_required
def purchase_requisitions_ui(request):
    """Enhanced Purchase requisition management interface with advanced filtering"""
    requisitions = PurchaseRequisition.objects.filter(company=request.user.company).order_by('-created_at')
    
    # Advanced filtering
    status_filter = request.GET.get('status', '')
    department_filter = request.GET.get('department', '')
    priority_filter = request.GET.get('priority', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if status_filter:
        requisitions = requisitions.filter(status=status_filter)
    
    if department_filter:
        requisitions = requisitions.filter(department=department_filter)
    
    if date_from:
        requisitions = requisitions.filter(created_at__date__gte=date_from)
    
    if date_to:
        requisitions = requisitions.filter(created_at__date__lte=date_to)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        requisitions = requisitions.filter(
            Q(pr_number__icontains=search_query) |
            Q(department__icontains=search_query) |
            Q(purpose__icontains=search_query) |
            Q(requested_by__first_name__icontains=search_query) |
            Q(requested_by__last_name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(requisitions, 25)
    page_number = request.GET.get('page')
    requisitions = paginator.get_page(page_number)
    
    # Statistics for dashboard
    stats = {
        'total': PurchaseRequisition.objects.filter(company=request.user.company).count(),
        'pending': PurchaseRequisition.objects.filter(company=request.user.company, status='pending_approval').count(),
        'approved': PurchaseRequisition.objects.filter(company=request.user.company, status='approved').count(),
        'draft': PurchaseRequisition.objects.filter(company=request.user.company, status='draft').count(),
    }
    
    # Department choices for filter
    departments = PurchaseRequisition.objects.filter(
        company=request.user.company
    ).values_list('department', flat=True).distinct()
    
    context = {
        'requisitions': requisitions,
        'status_choices': PurchaseRequisition.STATUS_CHOICES,
        'department_choices': [dept for dept in departments if dept],
        'priority_choices': [
            ('low', 'Low Priority'),
            ('medium', 'Medium Priority'),
            ('high', 'High Priority'),
            ('urgent', 'Urgent'),
        ],
        'filters': {
            'status': status_filter,
            'department': department_filter,
            'priority': priority_filter,
            'date_from': date_from,
            'date_to': date_to,
            'search': search_query,
        },
        'stats': stats,
        'can_create': request.user.has_perm('purchase.add_purchaserequisition'),
    }
    
    return render(request, 'purchase/requisitions-ui.html', context)

@login_required
def purchase_requisition_detail(request, pk):
    """Enhanced Purchase requisition detail view with comprehensive information"""
    requisition = get_object_or_404(PurchaseRequisition, pk=pk, company=request.user.company)
    
    # Check permissions
    can_approve = (
        request.user.has_perm('purchase.approve_requisition') and 
        requisition.status == 'pending_approval'
    )
    can_edit = (
        requisition.status == 'draft' and 
        (requisition.requested_by == request.user or request.user.has_perm('purchase.change_purchaserequisition'))
    )
    
    # Get related data
    items = requisition.items.all().select_related('product', 'preferred_supplier')
    
    # Approval history (if exists)
    approvals = PurchaseApproval.objects.filter(
        document_type='requisition',
        document_id=requisition.id
    ).order_by('-created_at')
    
    # Related RFQs if any
    related_rfqs = RequestForQuotation.objects.filter(
        purchase_requisition=requisition
    ).order_by('-created_at')
    
    context = {
        'requisition': requisition,
        'items': items,
        'can_approve': can_approve,
        'can_edit': can_edit,
        'approvals': approvals,
        'related_rfqs': related_rfqs,
        'total_items': items.count(),
    }
    
    return render(request, 'purchase/requisition-detail.html', context)

@login_required
def purchase_requisition_add(request):
    """Enhanced add purchase requisition with comprehensive form"""
    if request.method == 'POST':
        form = PurchaseRequisitionForm(request.POST, request.FILES, company=request.user.company)
        if form.is_valid():
            try:
                # Generate PR number
                last_pr = PurchaseRequisition.objects.filter(
                    company=request.user.company
                ).order_by('-id').first()
                pr_number = f"PR-{(last_pr.id + 1) if last_pr else 1:06d}"
                
                requisition = form.save(commit=False)
                requisition.company = request.user.company
                requisition.requested_by = request.user
                requisition.pr_number = pr_number
                
                # Set status based on action
                action = request.POST.get('action', 'save_draft')
                if action == 'submit':
                    requisition.status = 'pending_approval'
                else:
                    requisition.status = 'draft'
                
                requisition.save()
                
                # Handle custom fields
                requisition.priority = form.cleaned_data.get('priority', 'medium')
                requisition.justification = form.cleaned_data.get('justification', '')
                requisition.project_code = form.cleaned_data.get('project_code', '')
                requisition.estimated_budget = form.cleaned_data.get('estimated_budget', 0)
                requisition.urgency_reason = form.cleaned_data.get('urgency_reason', '')
                
                # Add items
                item_descriptions = request.POST.getlist('item_descriptions[]')
                quantities = request.POST.getlist('quantities[]')
                uoms = request.POST.getlist('uoms[]')
                estimated_costs = request.POST.getlist('estimated_costs[]')
                preferred_suppliers = request.POST.getlist('preferred_suppliers[]')
                item_notes = request.POST.getlist('item_notes[]')
                
                total_estimated_cost = 0
                for i, description in enumerate(item_descriptions):
                    if description and quantities[i]:
                        quantity = float(quantities[i])
                        estimated_cost = float(estimated_costs[i]) if estimated_costs[i] else 0
                        preferred_supplier_id = preferred_suppliers[i] if preferred_suppliers[i] else None
                        uom_id = uoms[i] if uoms[i] else None
                        
                        # Create a generic product entry or use existing logic
                        # This would need to be adapted based on your product model
                        # For now, assuming we're using item descriptions
                        
                        total_estimated_cost += quantity * estimated_cost
                
                requisition.total_estimated_cost = total_estimated_cost
                requisition.save()
                
                if action == 'submit':
                    messages.success(request, f'Purchase Requisition {pr_number} submitted for approval successfully.')
                else:
                    messages.success(request, f'Purchase Requisition {pr_number} saved as draft successfully.')
                
                return redirect('purchase:requisition_detail', pk=requisition.id)
                
            except Exception as e:
                messages.error(request, f'Error creating requisition: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PurchaseRequisitionForm(company=request.user.company)
    
    context = {
        'form': form,
        'title': 'Create Purchase Requisition',
        'unit_of_measures': UnitOfMeasure.objects.filter(company=request.user.company, is_active=True),
        'suppliers': Supplier.objects.filter(company=request.user.company, is_active=True),
        'today': timezone.now().date(),
    }
    return render(request, 'purchase/requisition-form.html', context)

@login_required
def purchase_requisition_edit(request, pk):
    """Edit existing purchase requisition"""
    requisition = get_object_or_404(PurchaseRequisition, pk=pk, company=request.user.company)
    
    # Check if user can edit
    if requisition.status != 'draft':
        messages.error(request, 'Only draft requisitions can be edited.')
        return redirect('purchase:requisition_detail', pk=pk)
    
    if requisition.requested_by != request.user and not request.user.has_perm('purchase.change_purchaserequisition'):
        messages.error(request, 'You do not have permission to edit this requisition.')
        return redirect('purchase:requisition_detail', pk=pk)
    
    if request.method == 'POST':
        form = PurchaseRequisitionForm(request.POST, request.FILES, instance=requisition, company=request.user.company)
        if form.is_valid():
            try:
                requisition = form.save(commit=False)
                
                # Set status based on action
                action = request.POST.get('action', 'save_draft')
                if action == 'submit':
                    requisition.status = 'pending_approval'
                else:
                    requisition.status = 'draft'
                
                requisition.save()
                
                # Handle items update (simplified for this example)
                # In a full implementation, you'd handle item updates properly
                
                if action == 'submit':
                    messages.success(request, f'Purchase Requisition {requisition.pr_number} updated and submitted for approval.')
                else:
                    messages.success(request, f'Purchase Requisition {requisition.pr_number} updated successfully.')
                
                return redirect('purchase:requisition_detail', pk=requisition.id)
                
            except Exception as e:
                messages.error(request, f'Error updating requisition: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PurchaseRequisitionForm(instance=requisition, company=request.user.company)
    
    context = {
        'form': form,
        'requisition': requisition,
        'title': f'Edit Purchase Requisition {requisition.pr_number}',
        'unit_of_measures': UnitOfMeasure.objects.filter(company=request.user.company, is_active=True),
        'suppliers': Supplier.objects.filter(company=request.user.company, is_active=True),
        'today': timezone.now().date(),
    }
    return render(request, 'purchase/requisition-form.html', context)

@login_required
@require_POST
def purchase_requisition_approve(request, pk):
    """Approve purchase requisition"""
    requisition = get_object_or_404(PurchaseRequisition, pk=pk, company=request.user.company)
    
    if request.user.has_perm('purchase.approve_requisition'):
        requisition.status = 'approved'
        requisition.approved_by = request.user
        requisition.approved_at = timezone.now()
        requisition.save()
        
        messages.success(request, f'Purchase Requisition {requisition.pr_number} approved successfully.')
    else:
        messages.error(request, 'You do not have permission to approve requisitions.')
    
    return redirect('purchase_requisition_detail', pk=pk)

# =====================================
# PURCHASE ORDER VIEWS
# =====================================

@login_required
def purchaseorders_ui(request):
    """Enhanced purchase order management interface"""
    orders = PurchaseOrder.objects.filter(company=request.user.company).order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        orders = orders.filter(
            Q(po_number__icontains=search_query) |
            Q(supplier__name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)
    
    # Initialize form for adding new purchase order
    form = PurchaseOrderForm()
    
    context = {
        'purchaseorders': orders,
        'suppliers': Supplier.objects.filter(company=request.user.company, is_active=True),
        'products': Product.objects.filter(company=request.user.company),
        'status_choices': PurchaseOrder.STATUS_CHOICES,
        'status_filter': status_filter,
        'search_query': search_query,
        'requisitions': PurchaseRequisition.objects.filter(
            company=request.user.company, 
            status='approved'
        ),
        'warehouses': Warehouse.objects.filter(company=request.user.company, is_active=True),
        'uoms': UnitOfMeasure.objects.filter(company=request.user.company, is_active=True),
        'form': form,
    }
    
    return render(request, 'purchase/purchaseorders-ui.html', context)

@login_required
def purchase_order_detail(request, pk):
    """Purchase order detail view"""
    order = get_object_or_404(PurchaseOrder, pk=pk, company=request.user.company)
    
    context = {
        'order': order,
        'items': order.items.all(),
        'tax_charges': order.tax_charges.all(),
        'grns': order.goodsreceiptnote_set.all(),
        'bills': order.bills.all(),
        'can_approve': request.user.has_perm('purchase.approve_purchase_order'),
    }
    
    return render(request, 'purchase/purchase-order-detail.html', context)

@login_required
def purchaseorders_add(request):
    """Enhanced purchase order creation with optional quotation and flexible item management"""
    rfq_id = request.GET.get('rfq')
    quotation_id = request.GET.get('quotation')
    
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, request.FILES, company=request.user.company)
        if form.is_valid():
            try:
                # Create purchase order
                order = form.save(commit=False)
                order.company = request.user.company
                order.created_by = request.user
                order.save()  # PO number will be auto-generated
                
                # Add items from form data
                products = request.POST.getlist('products[]')
                quantities = request.POST.getlist('quantities[]')
                unit_prices = request.POST.getlist('unit_prices[]')
                uoms = request.POST.getlist('uoms[]')
                quotation_items = request.POST.getlist('quotation_items[]')
                
                # Enhanced discount fields for items
                item_discount_types = request.POST.getlist('item_discount_types[]')
                item_discount_percentages = request.POST.getlist('item_discount_percentages[]')
                item_discount_amounts = request.POST.getlist('item_discount_amounts[]')
                item_discount_applications = request.POST.getlist('item_discount_applications[]')
                item_qty_discount_mins = request.POST.getlist('item_qty_discount_mins[]')
                item_qty_discount_rates = request.POST.getlist('item_qty_discount_rates[]')
                minimum_order_qtys = request.POST.getlist('minimum_order_qtys[]')
                
                subtotal = 0
                for i, product_id in enumerate(products):
                    if product_id and quantities[i]:
                        product = Product.objects.get(id=product_id)
                        quantity = Decimal(str(quantities[i]))
                        unit_price = Decimal(str(unit_prices[i]))
                        uom_id = uoms[i] if i < len(uoms) and uoms[i] else None
                        quotation_item_id = quotation_items[i] if i < len(quotation_items) and quotation_items[i] else None
                        
                        # Enhanced discount fields
                        item_discount_type = item_discount_types[i] if i < len(item_discount_types) else 'percentage'
                        item_discount_percentage = Decimal(str(item_discount_percentages[i])) if i < len(item_discount_percentages) and item_discount_percentages[i] else Decimal('0')
                        item_discount_amount = Decimal(str(item_discount_amounts[i])) if i < len(item_discount_amounts) and item_discount_amounts[i] else Decimal('0')
                        item_discount_application = item_discount_applications[i] if i < len(item_discount_applications) else 'subtract'
                        item_qty_discount_min = Decimal(str(item_qty_discount_mins[i])) if i < len(item_qty_discount_mins) and item_qty_discount_mins[i] else Decimal('0')
                        item_qty_discount_rate = Decimal(str(item_qty_discount_rates[i])) if i < len(item_qty_discount_rates) and item_qty_discount_rates[i] else Decimal('0')
                        minimum_order_qty = Decimal(str(minimum_order_qtys[i])) if i < len(minimum_order_qtys) and minimum_order_qtys[i] else Decimal('1')
                        
                        item = PurchaseOrderItem.objects.create(
                            purchase_order=order,
                            product=product,
                            quantity=quantity,
                            unit_price=unit_price,
                            uom_id=uom_id,
                            quotation_item_id=quotation_item_id,
                            item_discount_type=item_discount_type,
                            item_discount_percentage=item_discount_percentage,
                            item_discount_amount=item_discount_amount,
                            item_discount_application=item_discount_application,
                            item_qty_discount_min=item_qty_discount_min,
                            item_qty_discount_rate=item_qty_discount_rate,
                            minimum_order_qty=minimum_order_qty
                        )
                        subtotal += item.line_total
                
                # Add tax charges if specified
                tax_templates = request.POST.getlist('tax_templates[]')
                tax_amounts = request.POST.getlist('tax_amounts[]')
                
                total_tax = Decimal('0')
                for i, template_id in enumerate(tax_templates):
                    if template_id and tax_amounts[i]:
                        template = TaxChargesTemplate.objects.get(id=template_id)
                        amount = Decimal(str(tax_amounts[i]))
                        
                        PurchaseOrderTaxCharge.objects.create(
                            purchase_order=order,
                            tax_template=template,
                            amount=amount
                        )
                        total_tax += amount
                
                # Update order totals
                order.subtotal = subtotal
                order.tax_amount = total_tax
                
                # Enhanced discount calculation
                total_quantity = sum(item.quantity for item in order.items.all())
                discount_total = 0
                
                if order.discount_type == 'percentage' and order.discount_percentage > 0:
                    discount_total = order.subtotal * (order.discount_percentage / 100)
                elif order.discount_type == 'fixed_amount' and order.discount_amount > 0:
                    discount_total = order.discount_amount
                elif order.discount_type == 'quantity_based' and total_quantity >= order.quantity_discount_min_qty:
                    discount_total = order.subtotal * (order.quantity_discount_rate / 100)
                
                # Apply discount or rebate based on application type
                if order.discount_application == 'subtract':
                    order.discount_total = discount_total  # Discount
                    order.total_amount = order.subtotal - order.discount_total + order.tax_amount
                else:
                    order.discount_total = -discount_total  # Rebate/Fee (store as negative)
                    order.total_amount = order.subtotal + abs(order.discount_total) + order.tax_amount
                
                order.save()
                
                messages.success(request, f'Purchase Order {order.po_number} created successfully.')
                return redirect('purchase:purchase_order_detail', pk=order.id)
                
            except Exception as e:
                messages.error(request, f'Error creating purchase order: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PurchaseOrderForm(company=request.user.company)
        
        # Pre-fill form if coming from RFQ or Quotation (optional)
        if quotation_id:
            try:
                quotation = SupplierQuotation.objects.get(id=quotation_id, company=request.user.company)
                form.fields['supplier'].initial = quotation.supplier
                form.fields['purchase_requisition'].initial = quotation.rfq.purchase_requisition if quotation.rfq else None
                form.fields['supplier_quotation'].initial = quotation
                form.fields['payment_terms'].initial = quotation.payment_terms
                form.fields['delivery_terms'].initial = quotation.delivery_terms
                # Pre-fill discount fields from quotation
                form.fields['discount_type'].initial = quotation.discount_type
                form.fields['discount_percentage'].initial = quotation.discount_percentage
                form.fields['discount_amount'].initial = quotation.discount_amount
                form.fields['discount_application'].initial = quotation.discount_application
                form.fields['quantity_discount_min_qty'].initial = quotation.quantity_discount_min_qty
                form.fields['quantity_discount_rate'].initial = quotation.quantity_discount_rate
            except SupplierQuotation.DoesNotExist:
                messages.warning(request, 'Quotation not found.')
        elif rfq_id:
            try:
                rfq = RequestForQuotation.objects.get(id=rfq_id, company=request.user.company)
                form.fields['purchase_requisition'].initial = rfq.purchase_requisition
                form.fields['warehouse'].initial = rfq.warehouse
            except RequestForQuotation.DoesNotExist:
                messages.warning(request, 'RFQ not found.')
    
    context = {
        'form': form,
        'suppliers': Supplier.objects.filter(company=request.user.company, is_active=True),
        'products': Product.objects.filter(company=request.user.company),
        'requisitions': PurchaseRequisition.objects.filter(
            company=request.user.company, status='approved'
        ),
        'quotations': SupplierQuotation.objects.filter(
            company=request.user.company, status='submitted'
        ),
        'warehouses': Warehouse.objects.filter(company=request.user.company, is_active=True),
        'uoms': UnitOfMeasure.objects.filter(company=request.user.company, is_active=True),
        'tax_templates': TaxChargesTemplate.objects.filter(company=request.user.company, is_active=True),
        'title': 'Create Purchase Order',
        'rfq_id': rfq_id,
        'quotation_id': quotation_id,
    }
    return render(request, 'purchase/purchase-order-form.html', context)

@login_required
@require_POST
def purchase_order_approve(request, pk):
    """Approve purchase order"""
    order = get_object_or_404(PurchaseOrder, pk=pk, company=request.user.company)
    
    if request.user.has_perm('purchase.approve_purchase_order') or request.user.is_superuser:
        order.status = 'approved'
        order.approved_by = request.user
        order.approved_at = timezone.now()
        order.save()
        
        messages.success(request, f'Purchase Order {order.po_number} approved successfully.')
    else:
        messages.error(request, 'You do not have permission to approve purchase orders.')
    
    return redirect('purchase:purchase_order_detail', pk=pk)

@login_required
@require_POST
def purchase_order_cancel(request, pk):
    """Cancel purchase order"""
    order = get_object_or_404(PurchaseOrder, pk=pk, company=request.user.company)
    
    if order.can_be_cancelled():
        order.status = 'cancelled'
        order.save()
        
        messages.success(request, f'Purchase Order {order.po_number} cancelled successfully.')
    else:
        messages.error(request, 'This purchase order cannot be cancelled.')
    
    return redirect('purchase:purchase_order_detail', pk=pk)

@login_required
@require_POST
def purchase_order_send_to_supplier(request, pk):
    """Send purchase order to supplier"""
    order = get_object_or_404(PurchaseOrder, pk=pk, company=request.user.company)
    
    if order.status == 'approved':
        order.status = 'sent_to_supplier'
        order.save()
        
        # Here you could add email sending logic
        messages.success(request, f'Purchase Order {order.po_number} sent to supplier successfully.')
    else:
        messages.error(request, 'Only approved purchase orders can be sent to suppliers.')
    
    return redirect('purchase:purchase_order_detail', pk=pk)

@login_required
def purchase_order_edit(request, pk):
    """Edit purchase order (only if in draft status)"""
    order = get_object_or_404(PurchaseOrder, pk=pk, company=request.user.company)
    
    if order.status != 'draft':
        messages.error(request, 'Only draft purchase orders can be edited.')
        return redirect('purchase:purchase_order_detail', pk=pk)
    
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, request.FILES, instance=order)
        if form.is_valid():
            try:
                order = form.save()
                
                # Update items if needed
                # (Implementation similar to add view)
                
                messages.success(request, f'Purchase Order {order.po_number} updated successfully.')
                return redirect('purchase:purchase_order_detail', pk=order.id)
                
            except Exception as e:
                messages.error(request, f'Error updating purchase order: {str(e)}')
    else:
        form = PurchaseOrderForm(instance=order)
    
    context = {
        'form': form,
        'order': order,
        'suppliers': Supplier.objects.filter(company=request.user.company, is_active=True),
        'products': Product.objects.filter(company=request.user.company),
        'warehouses': Warehouse.objects.filter(company=request.user.company, is_active=True),
        'uoms': UnitOfMeasure.objects.filter(company=request.user.company, is_active=True),
        'tax_templates': TaxChargesTemplate.objects.filter(company=request.user.company, is_active=True),
        'title': f'Edit Purchase Order {order.po_number}',
        'is_edit': True,
    }
    return render(request, 'purchase/purchase-order-form.html', context)

@login_required
def purchase_order_duplicate(request, pk):
    """Duplicate a purchase order"""
    original_order = get_object_or_404(PurchaseOrder, pk=pk, company=request.user.company)
    
    # Create new order with same data
    new_order = PurchaseOrder.objects.create(
        company=original_order.company,
        supplier=original_order.supplier,
        purchase_requisition=original_order.purchase_requisition,
        warehouse=original_order.warehouse,
        created_by=request.user,
        expected_delivery_date=original_order.expected_delivery_date,
        delivery_terms=original_order.delivery_terms,
        payment_terms=original_order.payment_terms,
        purchase_limit=original_order.purchase_limit,
        discount_type=original_order.discount_type,
        discount_value=original_order.discount_value,
        notes=original_order.notes,
        terms_conditions=original_order.terms_conditions,
        status='draft'
    )
    
    # Duplicate items
    for item in original_order.items.all():
        PurchaseOrderItem.objects.create(
            purchase_order=new_order,
            product=item.product,
            quantity=item.quantity,
            uom=item.uom,
            unit_price=item.unit_price,
            item_discount=item.item_discount
        )
    
    # Duplicate tax charges
    for tax_charge in original_order.tax_charges.all():
        PurchaseOrderTaxCharge.objects.create(
            purchase_order=new_order,
            tax_template=tax_charge.tax_template,
            amount=tax_charge.amount
        )
    
    # Recalculate totals
    new_order.save()
    
    messages.success(request, f'Purchase Order duplicated as {new_order.po_number}.')
    return redirect('purchase:purchase_order_detail', pk=new_order.id)

# =====================================
# GOODS RECEIPT NOTE (GRN) VIEWS
# =====================================

@login_required
def grn_ui(request):
    """Goods Receipt Note management interface"""
    grns = GoodsReceiptNote.objects.filter(company=request.user.company).order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        grns = grns.filter(status=status_filter)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        grns = grns.filter(
            Q(grn_number__icontains=search_query) |
            Q(purchase_order__po_number__icontains=search_query) |
            Q(purchase_order__supplier__name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(grns, 20)
    page_number = request.GET.get('page')
    grns = paginator.get_page(page_number)
    
    context = {
        'grns': grns,
        'status_choices': GoodsReceiptNote.STATUS_CHOICES,
        'status_filter': status_filter,
        'search_query': search_query,
        'purchase_orders': PurchaseOrder.objects.filter(
            company=request.user.company,
            status__in=['approved', 'sent_to_supplier', 'partially_received']
        ),
        'pending_orders': PurchaseOrder.objects.filter(
            company=request.user.company,
            status__in=['approved', 'sent_to_supplier', 'partially_received']
        ),
        'warehouses': Warehouse.objects.filter(company=request.user.company, is_active=True),
    }
    
    return render(request, 'purchase/grns-ui.html', context)

@login_required
def grn_detail(request, pk):
    """GRN detail view"""
    grn = get_object_or_404(GoodsReceiptNote, pk=pk, company=request.user.company)
    
    context = {
        'grn': grn,
        'items': grn.items.all(),
    }
    
    return render(request, 'purchase/grn-detail.html', context)

@login_required
def grn_add(request):
    """Enhanced GRN creation with optional PO integration and tracking support"""
    if request.method == 'POST':
        try:
            # Determine mode (PO or manual)
            po_id = request.POST.get('purchase_order')
            supplier_id = request.POST.get('supplier')
            
            # Create GRN instance
            grn = GoodsReceiptNote.objects.create(
                company=request.user.company,
                received_by=request.user,
                received_date=request.POST.get('receipt_date', timezone.now().date()),
                vehicle_number=request.POST.get('vehicle_number', ''),
                gate_entry_number=request.POST.get('gate_entry_number', ''),
                supplier_delivery_note=request.POST.get('supplier_delivery_note', ''),
                transporter=request.POST.get('transporter', ''),
                driver_name=request.POST.get('driver_name', ''),
                driver_phone=request.POST.get('driver_phone', ''),
                requires_quality_inspection=request.POST.get('requires_quality_inspection') == 'on',
                notes=request.POST.get('notes', ''),
                warehouse_id=request.POST.get('warehouse'),
                status='inspection_pending' if request.POST.get('requires_quality_inspection') == 'on' else 'received'
            )
            
            # Set PO or supplier
            if po_id:
                grn.purchase_order_id = po_id
                grn.supplier = PurchaseOrder.objects.get(id=po_id).supplier
            elif supplier_id:
                grn.supplier_id = supplier_id
            
            grn.save()
            
            # Handle file uploads
            if request.FILES.get('delivery_challan'):
                grn.delivery_challan = request.FILES['delivery_challan']
            if request.FILES.get('packing_list'):
                grn.packing_list = request.FILES['packing_list']
            if request.FILES.get('quality_certificates'):
                grn.quality_certificates = request.FILES['quality_certificates']
            if request.FILES.get('photos_received_goods'):
                grn.photos_received_goods = request.FILES['photos_received_goods']
            
            grn.save()
            
            # Process items based on mode
            if po_id:
                # PO Mode - Process PO items
                po_item_ids = request.POST.getlist('po_item_ids[]')
                po_products = request.POST.getlist('po_products[]')
                po_received_quantities = request.POST.getlist('po_received_quantities[]')
                po_expiry_dates = request.POST.getlist('po_expiry_dates[]')
                po_batch_numbers = request.POST.getlist('po_batch_numbers[]')
                po_storage_locations = request.POST.getlist('po_storage_locations[]')
                po_item_notes = request.POST.getlist('po_item_notes[]')
                
                # Tracking data
                po_tracking_types = request.POST.getlist('po_tracking_types[]')
                po_tracking_numbers = request.POST.getlist('po_tracking_numbers[]')
                po_tracking_conditions = request.POST.getlist('po_tracking_conditions[]')
                po_tracking_notes = request.POST.getlist('po_tracking_notes[]')
                
                for i, po_item_id in enumerate(po_item_ids):
                    if i < len(po_received_quantities) and float(po_received_quantities[i]) > 0:
                        po_item = PurchaseOrderItem.objects.get(id=po_item_id)
                        received_qty = float(po_received_quantities[i])
                        
                        # Create GRN item
                        grn_item = GRNItem.objects.create(
                            grn=grn,
                            po_item=po_item,
                            product=po_item.product,
                            uom=po_item.uom,
                            ordered_qty=po_item.quantity,
                            received_qty=received_qty,
                            accepted_qty=received_qty,  # Initially all accepted
                            warehouse=grn.warehouse,
                            expiry_date=po_expiry_dates[i] if po_expiry_dates[i] else None,
                            location=po_storage_locations[i] if i < len(po_storage_locations) else '',
                            remarks=po_item_notes[i] if i < len(po_item_notes) else '',
                            quality_status='pending' if grn.requires_quality_inspection else 'passed'
                        )
                        
                        # Set batch number if provided
                        if i < len(po_batch_numbers) and po_batch_numbers[i]:
                            grn_item.tracking_type = 'batch'
                            grn_item.tracking_required = True
                            grn_item.save()
                            
                            # Create batch tracking
                            GRNItemTracking.objects.create(
                                grn_item=grn_item,
                                tracking_number=po_batch_numbers[i],
                                tracking_type='batch',
                                batch_number=po_batch_numbers[i],
                                quality_status='pending' if grn.requires_quality_inspection else 'passed'
                            )
                        
                        # Auto-set tracking based on product configuration
                        if po_item.product.tracking_method != 'none':
                            grn_item.tracking_type = po_item.product.tracking_method
                            grn_item.tracking_required = po_item.product.requires_individual_tracking
                            grn_item.save()
                        
                        # Create inventory lock for GRN item
                        # Lock items until purchase invoice is created
                        if grn.requires_quality_inspection:
                            # For items requiring quality inspection, lock all received quantity
                            # Items will be unlocked after quality inspection passes
                            lock_reason = 'quality_hold'
                            locked_quantity = received_qty
                        else:
                            # For items not requiring quality inspection, lock all received quantity
                            # Items will be unlocked when purchase invoice is created
                            lock_reason = 'pending_invoice'
                            locked_quantity = received_qty
                        
                        GRNInventoryLock.objects.create(
                            grn=grn,
                            grn_item=grn_item,
                            locked_quantity=locked_quantity,
                            lock_reason=lock_reason,
                            locked_by=request.user,
                            lock_notes=f'Auto-locked on GRN creation - {lock_reason}'
                        )
                        
                        # Update PO item received quantity
                        po_item.received_quantity = (po_item.received_quantity or 0) + received_qty
                        po_item.save()
                
                # Process individual tracking items
                tracking_item_index = 0
                for tracking_type, tracking_number, condition, tracking_note in zip(
                    po_tracking_types, po_tracking_numbers, po_tracking_conditions, po_tracking_notes
                ):
                    if tracking_number and tracking_item_index < len(po_item_ids):
                        # Find corresponding GRN item
                        item_index = tracking_item_index // 10  # Assuming max 10 tracking items per product
                        if item_index < len(po_item_ids):
                            grn_item = GRNItem.objects.filter(
                                grn=grn, 
                                po_item_id=po_item_ids[item_index]
                            ).first()
                            
                            if grn_item:
                                GRNItemTracking.objects.create(
                                    grn_item=grn_item,
                                    tracking_number=tracking_number,
                                    tracking_type=tracking_type,
                                    condition=condition,
                                    notes=tracking_note,
                                    quality_status='pending' if grn.requires_quality_inspection else 'passed'
                                )
                                
                                grn_item.tracking_required = True
                                grn_item.tracking_type = tracking_type
                                grn_item.save()
                    
                    tracking_item_index += 1
                
                # Update PO status
                po = PurchaseOrder.objects.get(id=po_id)
                po_items = po.items.all()
                all_received = all(
                    (item.received_quantity or 0) >= item.quantity for item in po_items
                )
                if all_received:
                    po.status = 'fully_received'
                else:
                    po.status = 'partially_received'
                po.save()
                
            else:
                # Manual Mode - Process manual items
                manual_products = request.POST.getlist('manual_products[]')
                manual_received_quantities = request.POST.getlist('manual_received_quantities[]')
                manual_uoms = request.POST.getlist('manual_uoms[]')
                manual_expiry_dates = request.POST.getlist('manual_expiry_dates[]')
                manual_batch_numbers = request.POST.getlist('manual_batch_numbers[]')
                manual_storage_locations = request.POST.getlist('manual_storage_locations[]')
                manual_item_notes = request.POST.getlist('manual_item_notes[]')
                
                # Tracking data
                manual_tracking_types = request.POST.getlist('manual_tracking_types[]')
                manual_tracking_numbers = request.POST.getlist('manual_tracking_numbers[]')
                manual_tracking_conditions = request.POST.getlist('manual_tracking_conditions[]')
                manual_tracking_notes = request.POST.getlist('manual_tracking_notes[]')
                
                for i, product_id in enumerate(manual_products):
                    if i < len(manual_received_quantities) and float(manual_received_quantities[i]) > 0:
                        product = Product.objects.get(id=product_id)
                        received_qty = float(manual_received_quantities[i])
                        
                        # Create GRN item
                        grn_item = GRNItem.objects.create(
                            grn=grn,
                            product=product,
                            uom_id=manual_uoms[i] if i < len(manual_uoms) else None,
                            received_qty=received_qty,
                            accepted_qty=received_qty,  # Initially all accepted
                            warehouse=grn.warehouse,
                            expiry_date=manual_expiry_dates[i] if i < len(manual_expiry_dates) and manual_expiry_dates[i] else None,
                            location=manual_storage_locations[i] if i < len(manual_storage_locations) else '',
                            remarks=manual_item_notes[i] if i < len(manual_item_notes) else '',
                            quality_status='pending' if grn.requires_quality_inspection else 'passed'
                        )
                        
                        # Set batch number if provided
                        if i < len(manual_batch_numbers) and manual_batch_numbers[i]:
                            grn_item.tracking_type = 'batch'
                            grn_item.tracking_required = True
                            grn_item.save()
                            
                            # Create batch tracking
                            GRNItemTracking.objects.create(
                                grn_item=grn_item,
                                tracking_number=manual_batch_numbers[i],
                                tracking_type='batch',
                                batch_number=manual_batch_numbers[i],
                                quality_status='pending' if grn.requires_quality_inspection else 'passed'
                            )
                        
                        # Create inventory lock for GRN item
                        # Lock items until purchase invoice is created
                        if grn.requires_quality_inspection:
                            # For items requiring quality inspection, lock all received quantity
                            # Items will be unlocked after quality inspection passes
                            lock_reason = 'quality_hold'
                            locked_quantity = received_qty
                        else:
                            # For items not requiring quality inspection, lock all received quantity
                            # Items will be unlocked when purchase invoice is created
                            lock_reason = 'pending_invoice'
                            locked_quantity = received_qty
                        
                        GRNInventoryLock.objects.create(
                            grn=grn,
                            grn_item=grn_item,
                            locked_quantity=locked_quantity,
                            lock_reason=lock_reason,
                            locked_by=request.user,
                            lock_notes=f'Auto-locked on GRN creation - {lock_reason}'
                        )
                
                # Process individual tracking items for manual mode
                tracking_item_index = 0
                for tracking_type, tracking_number, condition, tracking_note in zip(
                    manual_tracking_types, manual_tracking_numbers, manual_tracking_conditions, manual_tracking_notes
                ):
                    if tracking_number and tracking_item_index < len(manual_products):
                        # Find corresponding GRN item
                        item_index = tracking_item_index // 10  # Assuming max 10 tracking items per product
                        if item_index < len(manual_products):
                            grn_item = GRNItem.objects.filter(
                                grn=grn,
                                product_id=manual_products[item_index]
                            ).first()
                            
                            if grn_item:
                                GRNItemTracking.objects.create(
                                    grn_item=grn_item,
                                    tracking_number=tracking_number,
                                    tracking_type=tracking_type,
                                    condition=condition,
                                    notes=tracking_note,
                                    quality_status='pending' if grn.requires_quality_inspection else 'passed'
                                )
                                
                                grn_item.tracking_required = True
                                grn_item.tracking_type = tracking_type
                                grn_item.save()
                    
                    tracking_item_index += 1
            
            # Create quality inspection if required
            if grn.requires_quality_inspection:
                from .models import QualityInspection
                QualityInspection.objects.create(
                    grn=grn,
                    inspection_type='incoming',
                    priority='normal',
                    status='pending',
                    scheduled_date=timezone.now().date() + timedelta(days=1),
                    created_by=request.user
                )
            
            # Validate tracking quantities for all GRN items
            from django.core.exceptions import ValidationError
            validation_errors = []
            for grn_item in grn.items.all():
                try:
                    grn_item.validate_tracking_quantity()
                except ValidationError as e:
                    validation_errors.append(str(e))
            
            if validation_errors:
                # If there are validation errors, delete the GRN and show errors
                grn.delete()
                for error in validation_errors:
                    messages.error(request, error)
                return redirect('purchase:grn_add')
            
            messages.success(request, f'GRN {grn.grn_number} created successfully!')
            return redirect('purchase:grn_detail', pk=grn.id)
            
        except Exception as e:
            messages.error(request, f'Error creating GRN: {str(e)}')
            return redirect('purchase:grn_add')
    
    # GET request - show form
    context = {
        'purchase_orders': PurchaseOrder.objects.filter(
            company=request.user.company,
            status__in=['approved', 'sent_to_supplier', 'partially_received']
        ).select_related('supplier'),
        'suppliers': Supplier.objects.filter(company=request.user.company, is_active=True),
        'warehouses': Warehouse.objects.filter(company=request.user.company, is_active=True),
        'products': Product.objects.filter(company=request.user.company),
        'uoms': UnitOfMeasure.objects.filter(company=request.user.company, is_active=True),
        'today': timezone.now().date(),
        'title': 'Create Goods Receipt Note'
    }
    return render(request, 'purchase/grn-form.html', context)

# =====================================
# RETURNS VIEWS
# =====================================

@login_required
def returns_ui(request):
    """Returns management interface"""
    returns = PurchaseReturn.objects.filter(company=request.user.company).order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        returns = returns.filter(status=status_filter)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        returns = returns.filter(
            Q(return_number__icontains=search_query) |
            Q(grn__grn_number__icontains=search_query) |
            Q(grn__purchase_order__supplier__name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(returns, 20)
    page = request.GET.get('page')
    returns = paginator.get_page(page)
    
    context = {
        'returns': returns,
        'status_filter': status_filter,
        'search_query': search_query,
        'title': 'Purchase Returns'
    }
    return render(request, 'purchase/returns-ui.html', context)

@login_required
def return_detail(request, pk):
    """Return detail view"""
    return_obj = get_object_or_404(PurchaseReturn, pk=pk, company=request.user.company)
    
    context = {
        'return': return_obj,
        'title': f'Return {return_obj.return_number}'
    }
    return render(request, 'purchase/return-detail.html', context)

@login_required
def return_add(request):
    """Add new return"""
    grns = GoodsReceiptNote.objects.filter(
        company=request.user.company,
        status='received'
    ).select_related('purchase_order__supplier')
    
    if request.method == 'POST':
        # Handle form submission
        # This would contain the actual form processing logic
        messages.success(request, 'Return created successfully!')
        return redirect('purchase:returns_ui')
    
    context = {
        'grns': grns,
        'form_title': 'Create Purchase Return',
        'today': timezone.now().date(),
        'title': 'Create Return'
    }
    return render(request, 'purchase/return-form.html', context)

@login_required
def return_edit(request, pk):
    """Edit return"""
    return_obj = get_object_or_404(PurchaseReturn, pk=pk, company=request.user.company)
    
    if request.method == 'POST':
        # Handle form submission
        messages.success(request, 'Return updated successfully!')
        return redirect('purchase:return_detail', pk=pk)
    
    context = {
        'return': return_obj,
        'form_title': f'Edit Return {return_obj.return_number}',
        'title': 'Edit Return'
    }
    return render(request, 'purchase/return-form.html', context)

# =====================================
# QUALITY ASSURANCE VIEWS
# =====================================

@login_required
def quality_assurance(request):
    """Quality assurance dashboard"""
    inspections = QualityInspection.objects.filter(company=request.user.company).order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        inspections = inspections.filter(status=status_filter)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        inspections = inspections.filter(
            Q(inspection_number__icontains=search_query) |
            Q(grn__grn_number__icontains=search_query) |
            Q(grn__purchase_order__supplier__name__icontains=search_query)
        )
    
    # Statistics
    total_inspections = inspections.count()
    pending_inspections = inspections.filter(status='pending').count()
    in_progress_inspections = inspections.filter(status='in_progress').count()
    passed_inspections = inspections.filter(status='passed').count()
    failed_inspections = inspections.filter(status='failed').count()
    
    pass_rate = (passed_inspections / total_inspections * 100) if total_inspections > 0 else 0
    
    # Pagination
    paginator = Paginator(inspections, 20)
    page = request.GET.get('page')
    inspections = paginator.get_page(page)
    
    context = {
        'inspections': inspections,
        'status_filter': status_filter,
        'search_query': search_query,
        'total_inspections': total_inspections,
        'pending_inspections': pending_inspections,
        'in_progress_inspections': in_progress_inspections,
        'passed_inspections': passed_inspections,
        'failed_inspections': failed_inspections,
        'pass_rate': round(pass_rate, 1),
        'title': 'Quality Assurance'
    }
    return render(request, 'purchase/quality-assurance.html', context)

@login_required
def quality_inspection_conduct(request):
    """Conduct quality inspection"""
    # Get available GRNs that need inspection
    available_grns = GoodsReceiptNote.objects.filter(
        company=request.user.company,
        status='received',
        requires_quality_inspection=True
    ).select_related('purchase_order__supplier')
    
    if request.method == 'POST':
        # Handle inspection form submission
        messages.success(request, 'Quality inspection completed successfully!')
        return redirect('purchase:quality_assurance')
    
    # Mock inspection items for display
    inspection_items = []  # This would be populated based on selected GRN
    
    context = {
        'available_grns': available_grns,
        'inspection_items': inspection_items,
        'today': timezone.now().date(),
        'title': 'Conduct Quality Inspection'
    }
    return render(request, 'purchase/quality-inspection-conduct.html', context)

@login_required
def quality_inspection_form(request):
    """Quality inspection creation form"""
    available_grns = GoodsReceiptNote.objects.filter(
        company=request.user.company,
        status='received'
    ).select_related('purchase_order__supplier')
    
    # Get available inspectors (users who can perform inspections)
    from django.contrib.auth.models import User
    inspectors = User.objects.filter(is_active=True)
    
    if request.method == 'POST':
        # Handle form submission
        messages.success(request, 'Quality inspection created successfully!')
        return redirect('purchase:quality_assurance')
    
    context = {
        'available_grns': available_grns,
        'inspectors': inspectors,
        'form_title': 'Create Quality Inspection',
        'today': timezone.now().date(),
        'title': 'Create Quality Inspection'
    }
    return render(request, 'purchase/quality-inspection-form.html', context)

# =====================================
# BILL/INVOICE VIEWS
# =====================================

@login_required
def bills_ui(request):
    """Enhanced bills management interface"""
    bills = Bill.objects.filter(company=request.user.company).order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        bills = bills.filter(status=status_filter)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        bills = bills.filter(
            Q(bill_number__icontains=search_query) |
            Q(supplier__name__icontains=search_query) |
            Q(supplier_invoice_number__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(bills, 20)
    page_number = request.GET.get('page')
    bills = paginator.get_page(page_number)
    
    context = {
        'bills': bills,
        'status_choices': Bill.STATUS_CHOICES,
        'status_filter': status_filter,
        'search_query': search_query,
        'suppliers': Supplier.objects.filter(company=request.user.company, is_active=True),
        'received_grns': GoodsReceiptNote.objects.filter(
            company=request.user.company,
            status='accepted'
        ),
    }
    
    return render(request, 'purchase/bills-ui.html', context)

@login_required
def bill_detail(request, pk):
    """Bill detail view"""
    bill = get_object_or_404(Bill, pk=pk, company=request.user.company)
    
    context = {
        'bill': bill,
        'items': bill.items.all(),
        'payments': bill.payments.all(),
        'can_approve': request.user.has_perm('purchase.approve_bill'),
    }
    
    return render(request, 'purchase/bill-detail.html', context)

@login_required
def bill_add(request):
    """Enhanced bill creation with GRN/PO integration and tracking support"""
    if request.method == 'POST':
        form = BillForm(request.POST, request.FILES, user=request.user)
        
        if form.is_valid():
            try:
                # Create bill
                bill = form.save(commit=False)
                bill.company = request.user.company
                bill.created_by = request.user
                
                # Generate bill number
                last_bill = Bill.objects.filter(company=request.user.company).order_by('-id').first()
                bill.bill_number = f"BILL-{(last_bill.id + 1) if last_bill else 1:06d}"
                
                # Determine matching type
                if bill.purchase_order and bill.grn:
                    bill.matching_type = 'three_way'
                elif bill.purchase_order:
                    bill.matching_type = 'two_way_po'
                elif bill.grn:
                    bill.matching_type = 'two_way_grn'
                else:
                    bill.matching_type = 'standalone'
                
                bill.save()
                
                # Process items
                items_data = json.loads(request.POST.get('items_data', '[]'))
                tracking_data = json.loads(request.POST.get('tracking_data', '{}'))
                
                subtotal = Decimal('0.00')
                total_tax = Decimal('0.00')
                
                for item_data in items_data:
                    # Create bill item
                    item = BillItem.objects.create(
                        bill=bill,
                        product_id=item_data['product_id'],
                        quantity=Decimal(item_data['quantity']),
                        unit_price=Decimal(item_data['unit_price']),
                        item_source=item_data.get('item_source', 'manual'),
                        po_item_id=item_data.get('po_item_id'),
                        grn_item_id=item_data.get('grn_item_id'),
                        notes=item_data.get('notes', '')
                    )
                    
                    subtotal += item.line_total
                    
                    # Handle tracking for tracked products
                    item_tracking_list = tracking_data.get(str(item.id), [])
                    for tracking_info in item_tracking_list:
                        BillItemTracking.objects.create(
                            bill_item=item,
                            tracking_number=tracking_info['tracking_number'],
                            tracking_type=tracking_info['tracking_type'],
                            grn_tracking_id=tracking_info.get('grn_tracking_id'),
                            creates_asset=tracking_info.get('creates_asset', False),
                            asset_value=Decimal(tracking_info.get('asset_value', '0.00')),
                            batch_number=tracking_info.get('batch_number', ''),
                            manufacturing_date=tracking_info.get('manufacturing_date'),
                            expiry_date=tracking_info.get('expiry_date'),
                            warranty_expiry=tracking_info.get('warranty_expiry'),
                            condition=tracking_info.get('condition', 'new'),
                            notes=tracking_info.get('notes', '')
                        )
                    
                    # Release GRN inventory locks if applicable
                    if item.grn_item:
                        locks = GRNInventoryLock.objects.filter(
                            grn_item=item.grn_item,
                            is_released=False
                        )
                        for lock in locks:
                            lock.release_lock(bill)
                
                # Calculate totals
                bill.subtotal = subtotal
                bill.total_amount = subtotal + total_tax  # Add tax calculation logic
                bill.outstanding_amount = bill.total_amount
                bill.save()
                
                # Validate matching if applicable
                if bill.matching_type in ['three_way', 'two_way_po', 'two_way_grn']:
                    validation_result = bill.validate_three_way_match()
                    if not validation_result['is_valid']:
                        messages.warning(request, f'Matching validation warnings: {", ".join(validation_result["warnings"])}')
                
                messages.success(request, f'Bill {bill.bill_number} created successfully.')
                return redirect('bill_detail', pk=bill.id)
                
            except Exception as e:
                messages.error(request, f'Error creating bill: {str(e)}')
        else:
            # Form has errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = BillForm(user=request.user)
    
    # Prepare context data
    context = {
        'form': form,
        'suppliers': Supplier.objects.filter(company=request.user.company, is_active=True),
        'purchase_orders': PurchaseOrder.objects.filter(
            company=request.user.company,
            status__in=['approved', 'sent_to_supplier', 'partially_received', 'completed']
        ),
        'grns': GoodsReceiptNote.objects.filter(
            company=request.user.company,
            status__in=['completed', 'inspection_completed']
        ),
        'products': Product.objects.filter(company=request.user.company, is_active=True),
        'title': 'Create Purchase Invoice/Bill',
        'tracking_types': BillItemTracking.TRACKING_TYPE_CHOICES,
        'item_sources': BillItem.ITEM_SOURCE_CHOICES
    }
    return render(request, 'purchase/bill-form-enhanced.html', context)


@login_required
def bill_edit(request, pk):
    """Edit an existing bill"""
    bill = get_object_or_404(Bill, pk=pk, company=request.user.company)
    
    # Check if bill can be edited
    if bill.status not in ['draft', 'submitted']:
        messages.error(request, 'Only draft or submitted bills can be edited.')
        return redirect('bill_detail', pk=bill.pk)
    
    if request.method == 'POST':
        form = BillForm(request.POST, request.FILES, instance=bill, user=request.user)
        
        if form.is_valid():
            try:
                # Update bill
                bill = form.save(commit=False)
                
                # Determine matching type
                if bill.purchase_order and bill.grn:
                    bill.matching_type = 'three_way'
                elif bill.purchase_order:
                    bill.matching_type = 'two_way_po'
                elif bill.grn:
                    bill.matching_type = 'two_way_grn'
                else:
                    bill.matching_type = 'standalone'
                
                bill.save()
                
                # Clear existing items
                bill.items.all().delete()
                
                # Process updated items
                items_data = json.loads(request.POST.get('items_data', '[]'))
                tracking_data = json.loads(request.POST.get('tracking_data', '{}'))
                
                subtotal = Decimal('0.00')
                total_tax = Decimal('0.00')
                
                for item_data in items_data:
                    # Create bill item
                    item = BillItem.objects.create(
                        bill=bill,
                        product_id=item_data['product_id'],
                        quantity=Decimal(item_data['quantity']),
                        unit_price=Decimal(item_data['unit_price']),
                        item_source=item_data.get('item_source', 'manual'),
                        po_item_id=item_data.get('po_item_id'),
                        grn_item_id=item_data.get('grn_item_id'),
                        notes=item_data.get('notes', '')
                    )
                    
                    subtotal += item.line_total
                    
                    # Handle tracking for tracked products
                    item_tracking_list = tracking_data.get(str(item.id), [])
                    for tracking_info in item_tracking_list:
                        BillItemTracking.objects.create(
                            bill_item=item,
                            tracking_number=tracking_info['tracking_number'],
                            tracking_type=tracking_info['tracking_type'],
                            grn_tracking_id=tracking_info.get('grn_tracking_id'),
                            creates_asset=tracking_info.get('creates_asset', False),
                            asset_value=Decimal(tracking_info.get('asset_value', '0.00')),
                            batch_number=tracking_info.get('batch_number', ''),
                            manufacturing_date=tracking_info.get('manufacturing_date'),
                            expiry_date=tracking_info.get('expiry_date'),
                            warranty_expiry=tracking_info.get('warranty_expiry'),
                            condition=tracking_info.get('condition', 'new'),
                            notes=tracking_info.get('notes', '')
                        )
                
                # Update totals
                bill.subtotal = subtotal
                bill.total_amount = subtotal + total_tax  # Add tax calculation logic
                bill.outstanding_amount = bill.total_amount - bill.paid_amount
                bill.save()
                
                # Validate matching if applicable
                if bill.matching_type in ['three_way', 'two_way_po', 'two_way_grn']:
                    validation_result = bill.validate_three_way_match()
                    if not validation_result['is_valid']:
                        messages.warning(request, f'Matching validation warnings: {", ".join(validation_result["warnings"])}')
                
                messages.success(request, f'Bill {bill.bill_number} updated successfully.')
                return redirect('bill_detail', pk=bill.id)
                
            except Exception as e:
                messages.error(request, f'Error updating bill: {str(e)}')
        else:
            # Form has errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = BillForm(instance=bill, user=request.user)
    
    # Prepare context data including existing items
    existing_items = []
    for item in bill.items.all():
        item_data = {
            'product_id': item.product.id,
            'product_name': item.product.name,
            'product_sku': item.product.sku,
            'quantity': float(item.quantity),
            'unit_price': float(item.unit_price),
            'line_total': float(item.line_total),
            'item_source': item.item_source,
            'po_item_id': item.po_item.id if item.po_item else None,
            'grn_item_id': item.grn_item.id if item.grn_item else None,
            'notes': item.notes,
            'tracking_items': []
        }
        
        # Add tracking items
        for tracking in item.tracking_items.all():
            item_data['tracking_items'].append({
                'tracking_number': tracking.tracking_number,
                'tracking_type': tracking.tracking_type,
                'batch_number': tracking.batch_number,
                'manufacturing_date': tracking.manufacturing_date.strftime('%Y-%m-%d') if tracking.manufacturing_date else '',
                'expiry_date': tracking.expiry_date.strftime('%Y-%m-%d') if tracking.expiry_date else '',
                'condition': tracking.condition
            })
        
        existing_items.append(item_data)
    
    context = {
        'form': form,
        'bill': bill,
        'existing_items': json.dumps(existing_items),
        'suppliers': Supplier.objects.filter(company=request.user.company, is_active=True),
        'purchase_orders': PurchaseOrder.objects.filter(
            company=request.user.company,
            status__in=['approved', 'sent_to_supplier', 'partially_received', 'completed']
        ),
        'grns': GoodsReceiptNote.objects.filter(
            company=request.user.company,
            status__in=['completed', 'inspection_completed']
        ),
        'products': Product.objects.filter(company=request.user.company, is_active=True),
        'title': f'Edit Bill {bill.bill_number}',
        'tracking_types': BillItemTracking.TRACKING_TYPE_CHOICES,
        'item_sources': BillItem.ITEM_SOURCE_CHOICES,
        'is_edit': True
    }
    return render(request, 'purchase/bill-form-enhanced.html', context)

# =====================================
# PAYMENT VIEWS
# =====================================

@login_required
def payments_ui(request):
    """Enhanced payments management interface with supplier ledger"""
    payments = PurchasePayment.objects.filter(company=request.user.company).order_by('-created_at')
    
    # Filter by supplier
    supplier_filter = request.GET.get('supplier', '')
    if supplier_filter:
        payments = payments.filter(supplier_id=supplier_filter)
    
    # Filter by payment type
    payment_type_filter = request.GET.get('payment_type', '')
    if payment_type_filter:
        payments = payments.filter(payment_type=payment_type_filter)
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        payments = payments.filter(status=status_filter)
    
    # Date range filter
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        payments = payments.filter(payment_date__gte=date_from)
    if date_to:
        payments = payments.filter(payment_date__lte=date_to)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        payments = payments.filter(
            Q(payment_number__icontains=search_query) |
            Q(bill__bill_number__icontains=search_query) |
            Q(supplier__name__icontains=search_query) |
            Q(reference_number__icontains=search_query) |
            Q(transaction_id__icontains=search_query)
        )
    
    # Calculate summary statistics
    total_payments = payments.aggregate(total=Sum('amount'))['total'] or 0
    payment_count = payments.count()
    
    # Pagination
    paginator = Paginator(payments, 25)
    page_number = request.GET.get('page')
    payments = paginator.get_page(page_number)
    
    context = {
        'payments': payments,
        'search_query': search_query,
        'supplier_filter': supplier_filter,
        'payment_type_filter': payment_type_filter,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'total_payments': total_payments,
        'payment_count': payment_count,
        'suppliers': Supplier.objects.filter(company=request.user.company, is_active=True),
        'payment_methods': PurchasePayment.PAYMENT_METHOD_CHOICES,
        'payment_types': PurchasePayment.PAYMENT_TYPE_CHOICES,
        'payment_statuses': PurchasePayment.PAYMENT_STATUS_CHOICES,
        'unpaid_bills': Bill.objects.filter(
            company=request.user.company,
            status__in=['approved', 'submitted'],
            outstanding_amount__gt=0
        ),
    }
    
    return render(request, 'purchase/payments-ui.html', context)

@login_required
def payment_add(request):
    """Enhanced payment creation with supplier ledger integration"""
    if request.method == 'POST':
        form = PurchasePaymentForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            try:
                payment = form.save(commit=False)
                payment.company = request.user.company
                payment.created_by = request.user
                payment.paid_by = request.user
                
                # Set status based on payment method
                if payment.payment_method in ['cash', 'check']:
                    payment.status = 'completed'
                    payment.actual_date = payment.payment_date
                else:
                    payment.status = 'processing'
                
                payment.save()
                
                # Update bill if applicable
                if payment.bill:
                    bill = payment.bill
                    bill.paid_amount += payment.amount
                    bill.outstanding_amount = bill.total_amount - bill.paid_amount
                    
                    if bill.outstanding_amount <= 0:
                        bill.status = 'paid'
                    elif bill.paid_amount > 0:
                        bill.status = 'partially_paid'
                    
                    bill.save()
                
                # Check for overpayment warning
                if hasattr(form.cleaned_data, '_overpayment_warning'):
                    messages.warning(request, form.cleaned_data['_overpayment_warning'])
                
                messages.success(request, f'Payment {payment.payment_number} recorded successfully.')
                
                # Redirect based on payment type
                if payment.bill:
                    return redirect('purchase:bill_detail', pk=payment.bill.id)
                else:
                    return redirect('purchase:supplier_ledger', supplier_id=payment.supplier.id)
                
            except Exception as e:
                messages.error(request, f'Error recording payment: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = PurchasePaymentForm(user=request.user)
        
        # Pre-fill if coming from a specific bill
        bill_id = request.GET.get('bill_id')
        if bill_id:
            try:
                bill = Bill.objects.get(id=bill_id, company=request.user.company)
                form.fields['bill'].initial = bill
                form.fields['supplier'].initial = bill.supplier
                form.fields['amount'].initial = bill.outstanding_amount
            except Bill.DoesNotExist:
                messages.error(request, 'Bill not found.')
    
    context = {
        'form': form,
        'payment': PurchasePayment(),  # Empty payment object for template compatibility
        'suppliers': Supplier.objects.filter(company=request.user.company, is_active=True),
        'bills': Bill.objects.filter(
            company=request.user.company,
            status__in=['approved', 'submitted'],
            outstanding_amount__gt=0
        ),
        'title': 'Record Payment'
    }
    return render(request, 'purchase/payment-form.html', context)

@login_required
def payment_detail(request, pk):
    """Payment detail view"""
    payment = get_object_or_404(PurchasePayment, pk=pk, company=request.user.company)
    
    context = {
        'payment': payment,
        'title': f'Payment {payment.payment_number}'
    }
    return render(request, 'purchase/payment-detail.html', context)

@login_required
def payment_edit(request, pk):
    """Edit payment view"""
    payment = get_object_or_404(PurchasePayment, pk=pk, company=request.user.company)
    
    # Only allow editing of pending/processing payments
    if payment.status not in ['pending', 'processing']:
        messages.error(request, 'Cannot edit completed or cancelled payments.')
        return redirect('purchase:payment_detail', pk=pk)
    
    if request.method == 'POST':
        form = PurchasePaymentForm(request.POST, request.FILES, instance=payment, user=request.user)
        if form.is_valid():
            try:
                payment = form.save(commit=False)
                payment.updated_by = request.user
                payment.save()
                
                messages.success(request, f'Payment {payment.payment_number} updated successfully.')
                return redirect('purchase:payment_detail', pk=payment.pk)
                
            except Exception as e:
                messages.error(request, f'Error updating payment: {str(e)}')
    else:
        form = PurchasePaymentForm(instance=payment, user=request.user)
    
    context = {
        'form': form,
        'payment': payment,
        'suppliers': Supplier.objects.filter(company=request.user.company, is_active=True),
        'bills': Bill.objects.filter(
            company=request.user.company,
            status__in=['approved', 'submitted'],
            outstanding_amount__gt=0
        ),
        'title': f'Edit Payment {payment.payment_number}'
    }
    return render(request, 'purchase/payment-form.html', context)

@login_required
def payment_complete(request, pk):
    """Complete payment (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    try:
        payment = get_object_or_404(PurchasePayment, pk=pk, company=request.user.company)
        
        if payment.status == 'completed':
            return JsonResponse({'success': False, 'message': 'Payment is already completed'})
        
        if payment.status == 'cancelled':
            return JsonResponse({'success': False, 'message': 'Cannot complete cancelled payment'})
        
        payment.status = 'completed'
        payment.actual_date = timezone.now().date()
        payment.updated_by = request.user
        payment.save()
        
        # Update bill if applicable
        if payment.bill:
            bill = payment.bill
            bill.paid_amount += payment.amount
            bill.outstanding_amount = bill.total_amount - bill.paid_amount
            
            if bill.outstanding_amount <= 0:
                bill.status = 'paid'
            elif bill.paid_amount > 0:
                bill.status = 'partially_paid'
            
            bill.save()
        
        return JsonResponse({
            'success': True, 
            'message': f'Payment {payment.payment_number} completed successfully.'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
def payment_cancel(request, pk):
    """Cancel payment (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    try:
        payment = get_object_or_404(PurchasePayment, pk=pk, company=request.user.company)
        
        if payment.status == 'cancelled':
            return JsonResponse({'success': False, 'message': 'Payment is already cancelled'})
        
        if payment.status == 'completed':
            return JsonResponse({'success': False, 'message': 'Cannot cancel completed payment'})
        
        reason = request.POST.get('reason', '')
        if not reason:
            return JsonResponse({'success': False, 'message': 'Cancellation reason is required'})
        
        payment.status = 'cancelled'
        payment.notes = f"{payment.notes}\n\nCancelled: {reason}" if payment.notes else f"Cancelled: {reason}"
        payment.updated_by = request.user
        payment.save()
        
        return JsonResponse({
            'success': True, 
            'message': f'Payment {payment.payment_number} cancelled successfully.'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
def payment_delete(request, pk):
    """Delete payment (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    try:
        payment = get_object_or_404(PurchasePayment, pk=pk, company=request.user.company)
        
        if payment.status == 'completed':
            return JsonResponse({'success': False, 'message': 'Cannot delete completed payment'})
        
        payment_number = payment.payment_number
        payment.delete()
        
        return JsonResponse({
            'success': True, 
            'message': f'Payment {payment_number} deleted successfully.'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
def supplier_ledger(request, supplier_id=None):
    """Supplier ledger view with credit/debit tracking"""
    supplier = None
    ledger_entries = SupplierLedger.objects.filter(company=request.user.company)
    
    if supplier_id:
        supplier = get_object_or_404(Supplier, id=supplier_id, company=request.user.company)
        ledger_entries = ledger_entries.filter(supplier=supplier)
    
    # Filter form
    filter_form = SupplierLedgerFilterForm(request.GET, user=request.user)
    if filter_form.is_valid():
        if filter_form.cleaned_data['supplier']:
            ledger_entries = ledger_entries.filter(supplier=filter_form.cleaned_data['supplier'])
            supplier = filter_form.cleaned_data['supplier']
        
        if filter_form.cleaned_data['date_from']:
            ledger_entries = ledger_entries.filter(transaction_date__gte=filter_form.cleaned_data['date_from'])
        
        if filter_form.cleaned_data['date_to']:
            ledger_entries = ledger_entries.filter(transaction_date__lte=filter_form.cleaned_data['date_to'])
        
        if filter_form.cleaned_data['reference_type']:
            ledger_entries = ledger_entries.filter(reference_type=filter_form.cleaned_data['reference_type'])
        
        if filter_form.cleaned_data['search']:
            search = filter_form.cleaned_data['search']
            ledger_entries = ledger_entries.filter(
                Q(description__icontains=search) |
                Q(reference_number__icontains=search)
            )
    
    # Calculate totals
    totals = ledger_entries.aggregate(
        total_debit=Sum('debit_amount'),
        total_credit=Sum('credit_amount')
    )
    
    balance = (totals['total_debit'] or 0) - (totals['total_credit'] or 0)
    
    # Order by date
    ledger_entries = ledger_entries.order_by('-transaction_date', '-created_at')
    
    # Pagination
    paginator = Paginator(ledger_entries, 25)
    page_number = request.GET.get('page')
    ledger_entries = paginator.get_page(page_number)
    
    context = {
        'supplier': supplier,
        'ledger_entries': ledger_entries,
        'filter_form': filter_form,
        'total_debit': totals['total_debit'] or 0,
        'total_credit': totals['total_credit'] or 0,
        'balance': balance,
        'suppliers': Supplier.objects.filter(company=request.user.company, is_active=True),
        'title': f'Supplier Ledger - {supplier.name}' if supplier else 'Supplier Ledger'
    }
    return render(request, 'purchase/supplier-ledger.html', context)

# =====================================
# LEGACY VIEWS (Updated for compatibility)
# =====================================

@login_required
@require_POST
def purchaseorders_edit(request, pk):
    """Legacy PO edit for compatibility"""
    po = get_object_or_404(PurchaseOrder, pk=pk, company=request.user.company)
    
    try:
        po.supplier_id = request.POST.get('supplier_id')
        po.expected_delivery_date = request.POST.get('expected_delivery_date') if request.POST.get('expected_delivery_date') else None
        po.status = request.POST.get('status', po.status)
        po.notes = request.POST.get('notes', po.notes)
        po.save()
        
        return JsonResponse({
            'success': True,
            'purchaseorder': {
                'id': po.id,
                'po_number': po.po_number,
                'supplier': po.supplier.name if po.supplier else '',
                'supplier_id': po.supplier.id if po.supplier else '',
                'order_date': po.order_date.strftime('%Y-%m-%d') if po.order_date else '',
                'status': po.status
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def purchaseorders_delete(request, pk):
    """Legacy PO delete for compatibility"""
    po = get_object_or_404(PurchaseOrder, pk=pk, company=request.user.company)
    po.delete()
    return JsonResponse({'success': True})

# =====================================
# RFQ & QUOTATION MANAGEMENT VIEWS
# =====================================

@login_required
def rfq_ui(request):
    """Request for Quotation management interface"""
    try:
        company = request.user.company
        
        # Get filter parameters
        search = request.GET.get('search', '')
        status = request.GET.get('status', '')
        date_from = request.GET.get('date_from', '')
        
        # Build query
        rfqs = RequestForQuotation.objects.filter(company=company).select_related(
            'purchase_requisition', 'created_by', 'warehouse'
        ).prefetch_related(
            'suppliers', 'items__product', 'quotations'
        )
        
        if search:
            rfqs = rfqs.filter(
                Q(rfq_number__icontains=search) |
                Q(suppliers__name__icontains=search) |
                Q(description__icontains=search) |
                Q(purchase_requisition__pr_number__icontains=search)
            ).distinct()
        
        if status:
            rfqs = rfqs.filter(status=status)
            
        if date_from:
            rfqs = rfqs.filter(issue_date__gte=date_from)
        
        # Pagination
        paginator = Paginator(rfqs.order_by('-created_at'), 10)
        page_number = request.GET.get('page')
        rfqs = paginator.get_page(page_number)
        
        # Add statistics
        total_rfqs = RequestForQuotation.objects.filter(company=company).count()
        pending_rfqs = RequestForQuotation.objects.filter(company=company, status='sent').count()
        
        context = {
            'rfqs': rfqs,
            'search': search,
            'status': status,
            'date_from': date_from,
            'status_choices': RequestForQuotation.STATUS_CHOICES,
            'total_rfqs': total_rfqs,
            'pending_rfqs': pending_rfqs,
        }
        return render(request, 'purchase/rfq-ui.html', context)
    except Exception as e:
        messages.error(request, f'Error loading RFQs: {str(e)}')
        context = {
            'rfqs': [],
            'error': str(e),
            'status_choices': RequestForQuotation.STATUS_CHOICES,
        }
        return render(request, 'purchase/rfq-ui.html', context)

@login_required
def rfq_add(request):
    """Create new RFQ with enhanced PR integration"""
    if request.method == 'POST':
        if request.content_type == 'application/json':
            # Handle JSON requests (AJAX)
            try:
                data = json.loads(request.body)
                
                # Generate RFQ number
                last_rfq = RequestForQuotation.objects.filter(company=request.user.company).order_by('-id').first()
                rfq_number = data.get('rfq_number') or f"RFQ-{(last_rfq.id + 1) if last_rfq else 1:06d}"
                
                # Get Purchase Requisition if specified
                purchase_requisition = None
                if data.get('purchase_requisition_id'):
                    purchase_requisition = PurchaseRequisition.objects.get(
                        id=data['purchase_requisition_id'], 
                        company=request.user.company
                    )
                
                # Get warehouse
                warehouse = None
                if data.get('warehouse_id'):
                    warehouse = Warehouse.objects.get(id=data['warehouse_id'], company=request.user.company)
                elif purchase_requisition and purchase_requisition.warehouse:
                    warehouse = purchase_requisition.warehouse
                
                # Create RFQ
                rfq = RequestForQuotation.objects.create(
                    company=request.user.company,
                    rfq_number=rfq_number,
                    purchase_requisition=purchase_requisition,
                    warehouse=warehouse,
                    response_deadline=data.get('response_deadline'),
                    payment_terms=data.get('payment_terms', ''),
                    delivery_terms=data.get('delivery_terms', ''),
                    description=data.get('description', ''),
                    terms_and_conditions=data.get('terms_and_conditions', ''),
                    created_by=request.user
                )
                
                # Add suppliers
                supplier_ids = data.get('supplier_ids', [])
                for supplier_id in supplier_ids:
                    try:
                        supplier = Supplier.objects.get(id=supplier_id, company=request.user.company)
                        rfq.suppliers.add(supplier)
                    except:
                        pass
                
                # Add items
                items = data.get('items', [])
                for item_data in items:
                    try:
                        product = Product.objects.get(id=item_data['product_id'], company=request.user.company)
                        
                        # Get UOM if specified
                        required_uom = None
                        if item_data.get('uom_id'):
                            required_uom = UnitOfMeasure.objects.get(id=item_data['uom_id'], company=request.user.company)
                        
                        RFQItem.objects.create(
                            rfq=rfq,
                            product=product,
                            quantity=item_data['quantity'],
                            required_uom=required_uom,
                            specifications=item_data.get('specifications', ''),
                            priority=item_data.get('priority', 'medium'),
                            minimum_qty_required=item_data.get('minimum_qty_required', 1),
                            maximum_qty_acceptable=item_data.get('maximum_qty_acceptable', 0),
                            target_unit_price=item_data.get('target_unit_price', 0)
                        )
                    except Exception as e:
                        continue
                
                return JsonResponse({
                    'success': True,
                    'rfq_id': rfq.id,
                    'rfq_number': rfq.rfq_number
                })
            
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        else:
            # Handle form submission
            form = RequestForQuotationForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    # Generate RFQ number
                    last_rfq = RequestForQuotation.objects.filter(company=request.user.company).order_by('-id').first()
                    rfq_number = f"RFQ-{(last_rfq.id + 1) if last_rfq else 1:06d}"
                    
                    rfq = form.save(commit=False)
                    rfq.company = request.user.company
                    rfq.created_by = request.user
                    rfq.rfq_number = rfq_number
                    rfq.save()
                    
                    # Save many-to-many relationships
                    form.save_m2m()
                    
                    # Handle dynamic item creation from form data
                    products = request.POST.getlist('products[]')
                    quantities = request.POST.getlist('quantities[]')
                    uoms = request.POST.getlist('uoms[]')
                    priorities = request.POST.getlist('priorities[]')
                    target_prices = request.POST.getlist('target_prices[]')
                    specifications = request.POST.getlist('specifications[]')
                    min_quantities = request.POST.getlist('min_quantities[]')
                    max_quantities = request.POST.getlist('max_quantities[]')
                    
                    for i, product_id in enumerate(products):
                        if product_id and i < len(quantities) and quantities[i]:
                            try:
                                product = Product.objects.get(id=product_id, company=request.user.company)
                                
                                # Get UOM if specified
                                required_uom = None
                                if i < len(uoms) and uoms[i]:
                                    try:
                                        required_uom = UnitOfMeasure.objects.get(id=uoms[i], company=request.user.company)
                                    except UnitOfMeasure.DoesNotExist:
                                        pass
                                
                                RFQItem.objects.create(
                                    rfq=rfq,
                                    product=product,
                                    quantity=Decimal(quantities[i]),
                                    required_uom=required_uom,
                                    specifications=specifications[i] if i < len(specifications) else '',
                                    priority=priorities[i] if i < len(priorities) else 'medium',
                                    minimum_qty_required=Decimal(min_quantities[i]) if i < len(min_quantities) and min_quantities[i] else 1,
                                    maximum_qty_acceptable=Decimal(max_quantities[i]) if i < len(max_quantities) and max_quantities[i] else 0,
                                    target_unit_price=Decimal(target_prices[i]) if i < len(target_prices) and target_prices[i] else 0
                                )
                                
                            except Exception as e:
                                continue
                    
                    messages.success(request, f'RFQ {rfq_number} created successfully.')
                    return redirect('purchase:rfq_detail', pk=rfq.id)
                except Exception as e:
                    messages.error(request, f'Error creating RFQ: {str(e)}')
            else:
                messages.error(request, 'Please correct the errors below.')
    else:
        form = RequestForQuotationForm()
    
    # GET request - show form
    pr_id = request.GET.get('pr_id')
    purchase_requisition = None
    
    if pr_id:
        purchase_requisition = get_object_or_404(PurchaseRequisition, id=pr_id, company=request.user.company)
    
    suppliers = Supplier.objects.filter(company=request.user.company, is_active=True)
    products = Product.objects.filter(company=request.user.company)
    warehouses = Warehouse.objects.filter(company=request.user.company, is_active=True)
    requisitions = PurchaseRequisition.objects.filter(company=request.user.company, status='approved')
    uoms = UnitOfMeasure.objects.filter(company=request.user.company, is_active=True)
    
    context = {
        'form': form,
        'purchase_requisition': purchase_requisition,
        'suppliers': suppliers,
        'products': products,
        'warehouses': warehouses,
        'requisitions': requisitions,
        'uoms': uoms,
        'today': timezone.now().date(),
        'title': 'Create Request for Quotation'
    }
    return render(request, 'purchase/rfq-form.html', context)

@login_required
def rfq_detail(request, pk):
    """RFQ detail view with quotation comparison"""
    try:
        rfq = get_object_or_404(RequestForQuotation, pk=pk, company=request.user.company)
        
        # Get quotation comparison
        comparison = QuotationComparison(rfq)
        comparison_matrix = comparison.get_comparison_matrix()
        recommendations = comparison.get_best_quotation_analysis()
        
        context = {
            'rfq': rfq,
            'comparison_matrix': comparison_matrix,
            'recommendations': recommendations,
        }
        return render(request, 'purchase/rfq-detail.html', context)
    except Exception as e:
        return render(request, 'purchase/rfq-detail.html', {'error': str(e)})

@login_required
def rfq_edit(request, pk):
    """Edit existing RFQ"""
    try:
        rfq = get_object_or_404(RequestForQuotation, pk=pk, company=request.user.company)
        
        if request.method == 'POST':
            form = RequestForQuotationForm(request.POST, request.FILES, instance=rfq)
            if form.is_valid():
                updated_rfq = form.save(commit=False)
                updated_rfq.company = request.user.company
                updated_rfq.save()
                form.save_m2m()  # Save many-to-many relationships
                
                messages.success(request, f'RFQ {updated_rfq.rfq_number} updated successfully!')
                return redirect('purchase:rfq_detail', pk=updated_rfq.pk)
        else:
            form = RequestForQuotationForm(instance=rfq)
        
        # Get data for form
        suppliers = Supplier.objects.filter(company=request.user.company, is_active=True)
        warehouses = []
        purchase_requisitions = PurchaseRequisition.objects.filter(
            company=request.user.company, 
            status__in=['approved', 'partially_ordered']
        )
        
        try:
            from inventory.models import Warehouse
            warehouses = Warehouse.objects.filter(company=request.user.company, is_active=True)
        except ImportError:
            pass
        
        context = {
            'form': form,
            'rfq': rfq,
            'suppliers': suppliers,
            'warehouses': warehouses,
            'purchase_requisitions': purchase_requisitions,
            'is_edit': True,
        }
        return render(request, 'purchase/rfq-form.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading RFQ: {str(e)}')
        return redirect('purchase:rfq_ui')

@login_required
def quotations_ui(request):
    """Supplier Quotations management interface"""
    try:
        company = request.user.company
        
        # Get filter parameters
        search = request.GET.get('search', '')
        status = request.GET.get('status', '')
        supplier_id = request.GET.get('supplier_id', '')
        
        # Build query
        quotations = SupplierQuotation.objects.filter(company=company)
        
        if search:
            quotations = quotations.filter(
                Q(quotation_number__icontains=search) |
                Q(supplier__name__icontains=search) |
                Q(rfq__rfq_number__icontains=search)
            )
        
        if status:
            quotations = quotations.filter(status=status)
            
        if supplier_id:
            quotations = quotations.filter(supplier_id=supplier_id)
        
        # Pagination
        paginator = Paginator(quotations.order_by('-created_at'), 20)
        page_number = request.GET.get('page')
        quotations = paginator.get_page(page_number)
        
        # Get suppliers for filter
        suppliers = Supplier.objects.filter(company=company, is_active=True)
        
        context = {
            'quotations': quotations,
            'suppliers': suppliers,
            'search': search,
            'status': status,
            'supplier_id': supplier_id,
            'status_choices': SupplierQuotation.STATUS_CHOICES,
        }
        return render(request, 'purchase/quotations-ui.html', context)
    except Exception as e:
        context = {
            'quotations': [],
            'suppliers': [],
            'error': str(e)
        }
        return render(request, 'purchase/quotations-ui.html', context)

@login_required
def quotation_add(request):
    """Create supplier quotation with enhanced PR/RFQ integration"""
    if request.method == 'POST':
        if request.content_type == 'application/json':
            # Handle JSON requests (AJAX)
            try:
                data = json.loads(request.body)
                
                # Get RFQ and supplier
                rfq = get_object_or_404(RequestForQuotation, id=data['rfq_id'], company=request.user.company)
                supplier = get_object_or_404(Supplier, id=data['supplier_id'], company=request.user.company)
                
                # Generate quotation number
                last_quotation = SupplierQuotation.objects.filter(company=request.user.company).order_by('-id').first()
                quotation_number = data.get('quotation_number') or f"QT-{(last_quotation.id + 1) if last_quotation else 1:06d}"
                
                # Create quotation
                quotation = SupplierQuotation.objects.create(
                    company=request.user.company,
                    quotation_number=quotation_number,
                    rfq=rfq,
                    supplier=supplier,
                    quotation_date=data.get('quotation_date'),
                    valid_until=data.get('valid_until'),
                    payment_terms=data.get('payment_terms', ''),
                    delivery_terms=data.get('delivery_terms', ''),
                    delivery_time_days=data.get('delivery_time_days', 0),
                    discount_type=data.get('discount_type', 'percentage'),
                    discount_percentage=data.get('discount_percentage', 0),
                    discount_amount=data.get('discount_amount', 0),
                    notes=data.get('notes', '')
                )
                
                # Add quotation items
                total_amount = Decimal('0')
                items = data.get('items', [])
                
                for item_data in items:
                    try:
                        product = Product.objects.get(id=item_data['product_id'], company=request.user.company)
                        
                        # Find corresponding RFQ item
                        rfq_item = None
                        try:
                            rfq_item = RFQItem.objects.get(rfq=rfq, product=product)
                        except RFQItem.DoesNotExist:
                            pass
                        
                        # Get UOM if specified
                        quoted_uom = None
                        if item_data.get('uom_id'):
                            quoted_uom = UnitOfMeasure.objects.get(id=item_data['uom_id'], company=request.user.company)
                        
                        quote_item = SupplierQuotationItem.objects.create(
                            quotation=quotation,
                            rfq_item=rfq_item,
                            product=product,
                            quantity=item_data['quantity'],
                            unit_price=item_data['unit_price'],
                            quoted_uom=quoted_uom,
                            package_qty=item_data.get('package_qty', 1),
                            minimum_order_qty=item_data.get('minimum_order_qty', 1),
                            item_discount_percentage=item_data.get('item_discount_percentage', 0),
                            delivery_time_days=item_data.get('delivery_time_days', 0),
                            specifications=item_data.get('specifications', '')
                        )
                        
                        total_amount += quote_item.total_amount
                        
                    except Exception as e:
                        continue
                
                # Update quotation total
                quotation.total_amount = total_amount
                quotation.save()
                
                return JsonResponse({
                    'success': True,
                    'quotation_id': quotation.id,
                    'quotation_number': quotation.quotation_number
                })
            
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        else:
            # Handle form submission
            form = SupplierQuotationForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    quotation = form.save(commit=False)
                    quotation.company = request.user.company
                    
                    # Generate quotation number if not provided
                    if not quotation.quotation_number:
                        last_quotation = SupplierQuotation.objects.filter(company=request.user.company).order_by('-id').first()
                        quotation.quotation_number = f"QT-{(last_quotation.id + 1) if last_quotation else 1:06d}"
                    
                    quotation.save()
                    
                    # Handle dynamic item creation from form data
                    products = request.POST.getlist('products[]')
                    quantities = request.POST.getlist('quantities[]')
                    unit_prices = request.POST.getlist('unit_prices[]')
                    uoms = request.POST.getlist('uoms[]')
                    package_qtys = request.POST.getlist('package_qtys[]')
                    item_discounts = request.POST.getlist('item_discounts[]')
                    delivery_days = request.POST.getlist('delivery_days[]')
                    specifications = request.POST.getlist('specifications[]')
                    
                    total_amount = Decimal('0')
                    
                    for i, product_id in enumerate(products):
                        if product_id and i < len(quantities) and quantities[i]:
                            try:
                                product = Product.objects.get(id=product_id, company=request.user.company)
                                
                                # Find corresponding RFQ item
                                rfq_item = None
                                if quotation.rfq:
                                    try:
                                        rfq_item = RFQItem.objects.get(rfq=quotation.rfq, product=product)
                                    except RFQItem.DoesNotExist:
                                        pass
                                
                                # Get UOM if specified
                                quoted_uom = None
                                if i < len(uoms) and uoms[i]:
                                    try:
                                        quoted_uom = UnitOfMeasure.objects.get(id=uoms[i], company=request.user.company)
                                    except UnitOfMeasure.DoesNotExist:
                                        pass
                                
                                quote_item = SupplierQuotationItem.objects.create(
                                    quotation=quotation,
                                    rfq_item=rfq_item,
                                    product=product,
                                    quantity=Decimal(quantities[i]),
                                    unit_price=Decimal(unit_prices[i]) if i < len(unit_prices) and unit_prices[i] else 0,
                                    quoted_uom=quoted_uom,
                                    package_qty=Decimal(package_qtys[i]) if i < len(package_qtys) and package_qtys[i] else 1,
                                    item_discount_percentage=Decimal(item_discounts[i]) if i < len(item_discounts) and item_discounts[i] else 0,
                                    delivery_time_days=int(delivery_days[i]) if i < len(delivery_days) and delivery_days[i] else 0,
                                    specifications=specifications[i] if i < len(specifications) else ''
                                )
                                
                                total_amount += quote_item.total_amount
                                
                            except Exception as e:
                                continue
                    
                    # Update quotation total
                    quotation.total_amount = total_amount
                    quotation.save()
                    
                    messages.success(request, f'Quotation {quotation.quotation_number} created successfully.')
                    return redirect('purchase:quotation_detail', pk=quotation.id)
                except Exception as e:
                    messages.error(request, f'Error creating quotation: {str(e)}')
            else:
                messages.error(request, 'Please correct the errors below.')
    else:
        form = SupplierQuotationForm()
    
    # GET request - show form
    rfq_id = request.GET.get('rfq_id')
    supplier_id = request.GET.get('supplier_id')
    pr_id = request.GET.get('pr_id')
    
    rfq = None
    purchase_requisition = None
    
    if rfq_id:
        rfq = get_object_or_404(RequestForQuotation, id=rfq_id, company=request.user.company)
        if rfq.purchase_requisition:
            purchase_requisition = rfq.purchase_requisition
    elif pr_id:
        purchase_requisition = get_object_or_404(PurchaseRequisition, id=pr_id, company=request.user.company)
    
    suppliers = Supplier.objects.filter(company=request.user.company, is_active=True)
    rfqs = RequestForQuotation.objects.filter(company=request.user.company, status__in=['sent', 'responses_received'])
    uoms = UnitOfMeasure.objects.filter(company=request.user.company, is_active=True)
    products = Product.objects.filter(company=request.user.company)
    
    context = {
        'form': form,
        'rfq': rfq,
        'purchase_requisition': purchase_requisition,
        'suppliers': suppliers,
        'rfqs': rfqs,
        'supplier_id': supplier_id,
        'uoms': uoms,
        'products': products,
        'today': timezone.now().date(),
        'title': 'Create Supplier Quotation'
    }
    return render(request, 'purchase/quotation-form.html', context)

@login_required
def quotation_detail(request, pk):
    """Quotation detail view with UOM analysis"""
    try:
        quotation = get_object_or_404(SupplierQuotation, pk=pk, company=request.user.company)
        
        # Validate quotation
        validation = QuotationValidator.validate_quotation(quotation)
        
        # UOM conversion analysis for each item
        uom_analysis = []
        for item in quotation.items.all():
            analysis = UOMConverter.convert_quotation_to_base_units(item)
            uom_analysis.append({
                'item': item,
                'analysis': analysis
            })
        
        context = {
            'quotation': quotation,
            'validation': validation,
            'uom_analysis': uom_analysis,
        }
        return render(request, 'purchase/quotation-detail.html', context)
    except Exception as e:
        return render(request, 'purchase/quotation-detail.html', {'error': str(e)})

@login_required
def quotation_approve(request, pk):
    """Approve a supplier quotation"""
    try:
        quotation = get_object_or_404(SupplierQuotation, pk=pk, company=request.user.company)
        
        if request.method == 'POST':
            quotation.status = 'accepted'
            quotation.save()
            
            # Update RFQ status
            rfq = quotation.rfq
            rfq.status = 'responded'
            rfq.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Quotation {quotation.quotation_number} approved successfully'
            })
        
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def quotation_compare(request):
    """Compare quotations for an RFQ"""
    rfq_id = request.GET.get('rfq_id')
    
    if not rfq_id:
        return JsonResponse({'success': False, 'error': 'RFQ ID required'})
    
    try:
        rfq = get_object_or_404(RequestForQuotation, id=rfq_id, company=request.user.company)
        
        # Generate comparison
        comparison = QuotationComparison(rfq)
        comparison_matrix = comparison.get_comparison_matrix()
        recommendations = comparison.get_best_quotation_analysis()
        
        # Convert to JSON-serializable format
        comparison_data = []
        for product_data in comparison_matrix:
            product_comparison = {
                'product_id': product_data['product'].id,
                'product_name': product_data['product'].name,
                'required_qty': float(product_data['required_qty']),
                'required_uom': product_data['required_uom'],
                'quotations': []
            }
            
            for quote in product_data['quotations']:
                quote_data = {
                    'supplier_id': quote['supplier'].id,
                    'supplier_name': quote['supplier'].name,
                    'unit_price': float(quote['unit_price']),
                    'base_unit_price': float(quote['base_unit_price']),
                    'quoted_uom': quote['quoted_uom'],
                    'package_qty': float(quote['package_qty']),
                    'total_cost': float(quote['cost_for_required_qty']['total_cost']),
                    'lead_time': quote['lead_time'],
                }
                product_comparison['quotations'].append(quote_data)
            
            comparison_data.append(product_comparison)
        
        return JsonResponse({
            'success': True,
            'comparison_matrix': comparison_data,
            'recommendations': []  # Simplified for JSON response
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def quotation_to_po(request, pk):
    """Convert approved quotation to purchase order"""
    try:
        quotation = get_object_or_404(SupplierQuotation, pk=pk, company=request.user.company)
        
        if quotation.status != 'accepted':
            return JsonResponse({
                'success': False, 
                'error': 'Only accepted quotations can be converted to PO'
            })
        
        # Create PO from quotation
        po = PurchaseOrder.objects.create(
            company=request.user.company,
            supplier=quotation.supplier,
            supplier_quotation=quotation,
            created_by=request.user,
            payment_terms=quotation.payment_terms,
            subtotal=quotation.total_amount,
            total_amount=quotation.total_amount,
            notes=f"Generated from quotation {quotation.quotation_number}"
        )
        
        # Add PO items from quotation
        for quote_item in quotation.items.all():
            PurchaseOrderItem.objects.create(
                purchase_order=po,
                product=quote_item.product,
                quantity=quote_item.quantity,
                unit_price=quote_item.unit_price,
                discount_percentage=quote_item.discount_percentage
            )
        
        return JsonResponse({
            'success': True,
            'po_id': po.id,
            'message': f'Purchase Order {po.po_number} created from quotation'
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# =====================================
# ADDITIONAL FORM VIEWS FOR ENHANCED MODELS
# =====================================

@login_required
def unit_of_measure_ui(request):
    """Unit of Measure management interface"""
    uoms = UnitOfMeasure.objects.filter(company=request.user.company).order_by('uom_type', 'name')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        uoms = uoms.filter(
            Q(name__icontains=search_query) |
            Q(abbreviation__icontains=search_query) |
            Q(uom_type__icontains=search_query)
        )
    
    # Filter by type
    type_filter = request.GET.get('type', '')
    if type_filter:
        uoms = uoms.filter(uom_type=type_filter)
    
    # Pagination
    paginator = Paginator(uoms, 25)
    page_number = request.GET.get('page')
    uoms = paginator.get_page(page_number)
    
    form = UnitOfMeasureForm()
    
    context = {
        'uoms': uoms,
        'search_query': search_query,
        'type_filter': type_filter,
        'uom_types': UnitOfMeasure.UOM_TYPE_CHOICES,
        'form': form,
    }
    
    return render(request, 'purchase/uom-ui.html', context)

@login_required
def purchase_return_ui(request):
    """Purchase Return management interface"""
    returns = PurchaseReturn.objects.filter(company=request.user.company).order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        returns = returns.filter(status=status_filter)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        returns = returns.filter(
            Q(return_number__icontains=search_query) |
            Q(supplier__name__icontains=search_query) |
            Q(purchase_order__po_number__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(returns, 20)
    page_number = request.GET.get('page')
    returns = paginator.get_page(page_number)
    
    form = PurchaseReturnForm()
    
    context = {
        'returns': returns,
        'status_choices': PurchaseReturn.STATUS_CHOICES,
        'return_type_choices': PurchaseReturn.RETURN_TYPE_CHOICES,
        'status_filter': status_filter,
        'search_query': search_query,
        'suppliers': Supplier.objects.filter(company=request.user.company, is_active=True),
        'purchase_orders': PurchaseOrder.objects.filter(company=request.user.company),
        'form': form,
    }
    
    return render(request, 'purchase/returns-ui.html', context)

@login_required
def purchase_return_add(request):
    """Add new purchase return with file upload support"""
    if request.method == 'POST':
        form = PurchaseReturnForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Generate return number
                last_return = PurchaseReturn.objects.filter(company=request.user.company).order_by('-id').first()
                return_number = f"RET-{(last_return.id + 1) if last_return else 1:06d}"
                
                purchase_return = form.save(commit=False)
                purchase_return.company = request.user.company
                purchase_return.return_number = return_number
                purchase_return.created_by = request.user
                purchase_return.save()
                
                messages.success(request, f'Purchase Return {return_number} created successfully.')
                return redirect('purchase_return_detail', pk=purchase_return.id)
                
            except Exception as e:
                messages.error(request, f'Error creating purchase return: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PurchaseReturnForm()
    
    context = {
        'form': form,
        'suppliers': Supplier.objects.filter(company=request.user.company, is_active=True),
        'purchase_orders': PurchaseOrder.objects.filter(company=request.user.company),
        'grns': GoodsReceiptNote.objects.filter(company=request.user.company),
        'title': 'Create Purchase Return'
    }
    return render(request, 'purchase/return-form.html', context)

@login_required
def purchase_return_detail(request, pk):
    """Purchase return detail view"""
    purchase_return = get_object_or_404(PurchaseReturn, pk=pk, company=request.user.company)
    
    context = {
        'return': purchase_return,
        'items': purchase_return.items.all(),
        'can_approve': request.user.has_perm('purchase.approve_return'),
    }
    
    return render(request, 'purchase/return-detail.html', context)

@login_required
def supplier_detail(request, pk):
    """Supplier detail view"""
    supplier = get_object_or_404(Supplier, pk=pk, company=request.user.company)
    
    # Get related data
    recent_orders = PurchaseOrder.objects.filter(supplier=supplier).order_by('-created_at')[:10]
    recent_quotations = SupplierQuotation.objects.filter(supplier=supplier).order_by('-created_at')[:10]
    recent_bills = Bill.objects.filter(supplier=supplier).order_by('-created_at')[:10]
    
    # Calculate metrics
    total_orders = PurchaseOrder.objects.filter(supplier=supplier).count()
    total_amount = PurchaseOrder.objects.filter(supplier=supplier).aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    context = {
        'supplier': supplier,
        'recent_orders': recent_orders,
        'recent_quotations': recent_quotations,
        'recent_bills': recent_bills,
        'total_orders': total_orders,
        'total_amount': total_amount,
    }
    
    return render(request, 'purchase/supplier-detail.html', context)

# =====================================
# API ENDPOINTS FOR AJAX OPERATIONS
# =====================================

@login_required
def get_po_items_ajax(request):
    """Get PO items for GRN creation"""
    po_id = request.GET.get('po_id')
    if not po_id:
        return JsonResponse({'success': False, 'error': 'No PO ID provided'})
    
    try:
        po = PurchaseOrder.objects.get(id=po_id, company=request.user.company)
        items = []
        
        for item in po.items.all():
            pending_quantity = item.quantity - (item.received_quantity or 0)
            items.append({
                'id': item.id,
                'product_id': item.product.id,
                'product_name': item.product.name,
                'product_code': getattr(item.product, 'code', ''),
                'ordered_quantity': float(item.quantity),
                'received_quantity': float(item.received_quantity or 0),
                'pending_quantity': float(pending_quantity),
                'uom': item.uom.name if item.uom else 'Unit'
            })
        
        return JsonResponse({
            'success': True,
            'supplier_id': po.supplier.id,
            'supplier_name': po.supplier.name,
            'items': items
        })
    except PurchaseOrder.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Purchase Order not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def get_rfq_items_ajax(request, rfq_id):
    """Get RFQ items for quotation creation"""
    try:
        rfq = get_object_or_404(RequestForQuotation, id=rfq_id, company=request.user.company)
        items = []
        
        for item in rfq.items.all():
            items.append({
                'id': item.id,
                'product_id': item.product.id,
                'product_name': item.product.name,
                'quantity': float(item.quantity),
                'required_uom': item.required_uom.name if item.required_uom else '',
                'specifications': item.specifications,
                'priority': item.priority,
                'minimum_qty_required': float(item.minimum_qty_required),
                'target_unit_price': float(item.target_unit_price) if item.target_unit_price else 0,
            })
        
        return JsonResponse({'success': True, 'items': items})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def supplier_search_ajax(request):
    """Search suppliers for AJAX requests"""
    query = request.GET.get('q', '')
    suppliers = Supplier.objects.filter(
        company=request.user.company,
        is_active=True,
        name__icontains=query
    )[:10]
    
    return JsonResponse({
        'suppliers': [
            {'id': supplier.id, 'name': supplier.name}
            for supplier in suppliers
        ]
    })


# =====================================
# QUALITY INSPECTION VIEWS
# =====================================

@login_required
def quality_inspection_dashboard(request):
    """Quality inspection dashboard showing pending inspections"""
    pending_inspections = QualityInspection.objects.filter(
        grn__company=request.user.company,
        status__in=['pending', 'in_progress']
    ).select_related('grn', 'assigned_to').order_by('scheduled_date')
    
    completed_inspections = QualityInspection.objects.filter(
        grn__company=request.user.company,
        status='completed'
    ).select_related('grn', 'assigned_to').order_by('-completed_at')[:10]
    
    # Statistics
    total_pending = pending_inspections.count()
    overdue_inspections = pending_inspections.filter(
        scheduled_date__lt=timezone.now()
    ).count()
    
    context = {
        'pending_inspections': pending_inspections,
        'completed_inspections': completed_inspections,
        'total_pending': total_pending,
        'overdue_inspections': overdue_inspections,
        'title': 'Quality Inspection Dashboard'
    }
    return render(request, 'purchase/quality-inspection-dashboard.html', context)


@login_required
def quality_inspection_detail(request, pk):
    """Quality inspection detail and result recording"""
    inspection = get_object_or_404(
        QualityInspection, 
        pk=pk, 
        grn__company=request.user.company
    )
    
    if request.method == 'POST':
        formset = QualityInspectionResultFormSet(request.POST, request.FILES, instance=inspection)
        
        if formset.is_valid():
            try:
                # Save inspection results
                results = formset.save()
                
                # Update inspection status
                inspection.status = 'completed'
                inspection.completed_at = timezone.now()
                inspection.completed_by = request.user
                inspection.save()
                
                # Update GRN status based on inspection results
                grn = inspection.grn
                all_passed = all(
                    result.action_taken == 'accept' for result in results
                )
                any_rejected = any(
                    result.action_taken == 'reject' for result in results
                )
                
                if all_passed:
                    grn.status = 'inspection_completed'
                elif any_rejected:
                    grn.status = 'inspection_completed'  # Will handle returns separately
                
                grn.save()
                
                # Update individual GRN items quality status
                for result in results:
                    grn_item = result.grn_item
                    if result.action_taken == 'accept':
                        grn_item.quality_status = 'passed'
                    elif result.action_taken == 'reject':
                        grn_item.quality_status = 'failed'
                    elif result.action_taken == 'rework':
                        grn_item.quality_status = 'rework_required'
                    grn_item.save()
                
                messages.success(request, 'Quality inspection completed successfully.')
                return redirect('quality_inspection_dashboard')
                
            except Exception as e:
                messages.error(request, f'Error completing inspection: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        formset = QualityInspectionResultFormSet(instance=inspection)
    
    context = {
        'inspection': inspection,
        'formset': formset,
        'grn_items': inspection.grn.items.all(),
        'title': f'Quality Inspection - {inspection.grn.grn_number}'
    }
    return render(request, 'purchase/quality-inspection-detail.html', context)


@login_required
def quality_inspection_assign(request, grn_pk):
    """Assign quality inspection for a GRN"""
    grn = get_object_or_404(GoodsReceiptNote, pk=grn_pk, company=request.user.company)
    
    if request.method == 'POST':
        form = QualityInspectionForm(request.POST)
        if form.is_valid():
            try:
                inspection = form.save(commit=False)
                inspection.grn = grn
                inspection.created_by = request.user
                inspection.save()
                
                # Update GRN status
                grn.status = 'under_inspection'
                grn.save()
                
                messages.success(request, 'Quality inspection assigned successfully.')
                return redirect('grn_detail', pk=grn.id)
                
            except Exception as e:
                messages.error(request, f'Error assigning inspection: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = QualityInspectionForm(initial={'grn': grn})
    
    context = {
        'form': form,
        'grn': grn,
        'title': f'Assign Quality Inspection - {grn.grn_number}'
    }
    return render(request, 'purchase/quality-inspection-assign.html', context)


# =====================================
# PURCHASE RETURN VIEWS
# =====================================

@login_required
def purchase_returns_ui(request):
    """Purchase returns management interface"""
    returns = PurchaseReturn.objects.filter(
        company=request.user.company
    ).select_related('supplier', 'grn', 'quality_inspection').order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        returns = returns.filter(status=status_filter)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        returns = returns.filter(
            Q(return_number__icontains=search_query) |
            Q(supplier__name__icontains=search_query) |
            Q(reason__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(returns, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_choices': PurchaseReturn.STATUS_CHOICES,
        'title': 'Purchase Returns'
    }
    return render(request, 'purchase/purchase-returns-ui.html', context)


@login_required
def purchase_return_detail(request, pk):
    """Purchase return detail view"""
    return_obj = get_object_or_404(
        PurchaseReturn, 
        pk=pk, 
        company=request.user.company
    )
    
    context = {
        'return': return_obj,
        'items': return_obj.items.all(),
        'title': f'Purchase Return - {return_obj.return_number}'
    }
    return render(request, 'purchase/purchase-return-detail.html', context)


# =====================================
# AJAX HELPER VIEWS
# =====================================

@login_required
def get_grn_items_ajax(request):
    """Get GRN items for return creation"""
    grn_id = request.GET.get('grn_id')
    if not grn_id:
        return JsonResponse({'success': False, 'error': 'No GRN ID provided'})
    
    try:
        grn = GoodsReceiptNote.objects.get(id=grn_id, company=request.user.company)
        items = []
        
        for item in grn.items.all():
            returnable_quantity = item.received_quantity - (item.returned_quantity or 0)
            if returnable_quantity > 0:
                items.append({
                    'id': item.id,
                    'product_name': item.product.name,
                    'product_code': item.product.code,
                    'received_quantity': float(item.received_quantity),
                    'returned_quantity': float(item.returned_quantity or 0),
                    'returnable_quantity': float(returnable_quantity),
                    'quality_status': item.quality_status
                })
        
        return JsonResponse({
            'success': True,
            'supplier_id': grn.supplier.id if grn.supplier else grn.purchase_order.supplier.id,
            'items': items
        })
    except GoodsReceiptNote.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'GRN not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    results = [{'id': s.id, 'text': s.name} for s in suppliers]
    return JsonResponse({'results': results})

@login_required
def product_search_ajax(request):
    """Search products for AJAX requests"""
    query = request.GET.get('q', '')
    products = Product.objects.filter(
        company=request.user.company,
        name__icontains=query
    )[:10]
    
    results = [{'id': p.id, 'text': p.name} for p in products]
    return JsonResponse({'results': results})


# =====================================
# BILL AJAX ENDPOINTS
# =====================================

@login_required
def get_po_items_ajax(request):
    """Get PO items for bill creation"""
    po_id = request.GET.get('po_id')
    if not po_id:
        return JsonResponse({'success': False, 'error': 'No PO ID provided'})
    
    try:
        po = PurchaseOrder.objects.get(id=po_id, company=request.user.company)
        items = []
        
        for item in po.items.all():
            # Calculate pending quantity to invoice
            invoiced_qty = BillItem.objects.filter(
                po_item=item,
                bill__status__in=['draft', 'submitted', 'approved', 'paid']
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            pending_qty = item.quantity - invoiced_qty
            
            if pending_qty > 0:
                items.append({
                    'id': item.id,
                    'product_id': item.product.id,
                    'product_name': item.product.name,
                    'product_code': item.product.code,
                    'ordered_quantity': float(item.quantity),
                    'invoiced_quantity': float(invoiced_qty),
                    'pending_quantity': float(pending_qty),
                    'unit_price': float(item.unit_price),
                    'tracking_required': item.product.is_tracked(),
                    'tracking_method': item.product.tracked_by
                })
        
        return JsonResponse({
            'success': True,
            'supplier_id': po.supplier.id,
            'items': items
        })
    except PurchaseOrder.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Purchase Order not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def get_grn_items_for_bill_ajax(request):
    """Get GRN items for bill creation"""
    grn_id = request.GET.get('grn_id')
    if not grn_id:
        return JsonResponse({'success': False, 'error': 'No GRN ID provided'})
    
    try:
        grn = GoodsReceiptNote.objects.get(id=grn_id, company=request.user.company)
        items = []
        
        for item in grn.items.all():
            # Calculate pending quantity to invoice
            invoiced_qty = BillItem.objects.filter(
                grn_item=item,
                bill__status__in=['draft', 'submitted', 'approved', 'paid']
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            pending_qty = item.received_qty - invoiced_qty
            
            if pending_qty > 0:
                # Get tracking information
                tracking_data = []
                for tracking in item.tracking.all():
                    tracking_data.append({
                        'id': tracking.id,
                        'tracking_number': tracking.tracking_number,
                        'tracking_type': tracking.tracking_type,
                        'batch_number': tracking.batch_number,
                        'manufacturing_date': tracking.manufacturing_date.isoformat() if tracking.manufacturing_date else None,
                        'expiry_date': tracking.expiry_date.isoformat() if tracking.expiry_date else None,
                        'condition': tracking.condition
                    })
                
                items.append({
                    'id': item.id,
                    'product_id': item.product.id,
                    'product_name': item.product.name,
                    'product_code': item.product.code,
                    'received_quantity': float(item.received_qty),
                    'invoiced_quantity': float(invoiced_qty),
                    'pending_quantity': float(pending_qty),
                    'tracking_required': item.product.is_tracked(),
                    'tracking_method': item.product.tracked_by,
                    'tracking_data': tracking_data
                })
        
        return JsonResponse({
            'success': True,
            'supplier_id': grn.supplier.id if grn.supplier else grn.purchase_order.supplier.id,
            'po_id': grn.purchase_order.id if grn.purchase_order else None,
            'items': items
        })
    except GoodsReceiptNote.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'GRN not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def filter_po_and_grn_ajax(request):
    """Filter POs and GRNs by supplier"""
    supplier_id = request.GET.get('supplier_id')
    if not supplier_id:
        return JsonResponse({'success': False, 'error': 'No supplier ID provided'})
    
    try:
        # Get POs for supplier
        pos = PurchaseOrder.objects.filter(
            company=request.user.company,
            supplier_id=supplier_id,
            status__in=['approved', 'sent_to_supplier', 'partially_received', 'completed']
        ).values('id', 'order_number', 'order_date')
        
        # Get GRNs for supplier
        grns = GoodsReceiptNote.objects.filter(
            company=request.user.company,
            supplier_id=supplier_id,
            status__in=['completed', 'inspection_completed']
        ).values('id', 'grn_number', 'received_date')
        
        return JsonResponse({
            'success': True,
            'purchase_orders': list(pos),
            'grns': list(grns)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def validate_bill_matching_ajax(request):
    """Validate bill matching constraints"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'})
    
    try:
        data = json.loads(request.body)
        po_id = data.get('po_id')
        grn_id = data.get('grn_id')
        supplier_id = data.get('supplier_id')
        items = data.get('items', [])
        
        warnings = []
        errors = []
        
        # Validate PO and GRN relationship
        if po_id and grn_id:
            try:
                po = PurchaseOrder.objects.get(id=po_id, company=request.user.company)
                grn = GoodsReceiptNote.objects.get(id=grn_id, company=request.user.company)
                
                if grn.purchase_order_id != po_id:
                    errors.append('Selected GRN must be from the selected Purchase Order')
                
                if po.supplier_id != int(supplier_id):
                    errors.append('Purchase Order supplier must match selected supplier')
                    
            except (PurchaseOrder.DoesNotExist, GoodsReceiptNote.DoesNotExist):
                errors.append('Invalid PO or GRN selection')
        
        # Validate item quantities
        for item in items:
            if item.get('po_item_id') and item.get('quantity'):
                try:
                    po_item = PurchaseOrderItem.objects.get(id=item['po_item_id'])
                    if float(item['quantity']) > po_item.quantity:
                        warnings.append(f'Item {po_item.product.name}: Invoice quantity exceeds PO quantity')
                except PurchaseOrderItem.DoesNotExist:
                    errors.append(f'Invalid PO item reference')
            
            if item.get('grn_item_id') and item.get('quantity'):
                try:
                    grn_item = GRNItem.objects.get(id=item['grn_item_id'])
                    if float(item['quantity']) > grn_item.received_qty:
                        warnings.append(f'Item {grn_item.product.name}: Invoice quantity exceeds received quantity')
                except GRNItem.DoesNotExist:
                    errors.append(f'Invalid GRN item reference')
        
        return JsonResponse({
            'success': True,
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def get_supplier_pos_ajax(request):
    """Get Purchase Orders for a specific supplier"""
    supplier_id = request.GET.get('supplier_id')
    if not supplier_id:
        return JsonResponse({'success': False, 'error': 'Supplier ID required'})
    
    try:
        pos = PurchaseOrder.objects.filter(
            company=request.user.company,
            supplier_id=supplier_id,
            status__in=['approved', 'sent_to_supplier', 'partially_received', 'completed']
        ).values('id', 'po_number', 'status', 'po_date', 'total_amount')
        
        return JsonResponse({
            'success': True,
            'pos': list(pos)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def get_supplier_grns_ajax(request):
    """Get GRNs for a specific supplier"""
    supplier_id = request.GET.get('supplier_id')
    if not supplier_id:
        return JsonResponse({'success': False, 'error': 'Supplier ID required'})
    
    try:
        grns = GoodsReceiptNote.objects.filter(
            company=request.user.company,
            supplier_id=supplier_id,
            status__in=['completed', 'inspection_completed']
        ).values('id', 'grn_number', 'status', 'received_date')
        
        return JsonResponse({
            'success': True,
            'grns': list(grns)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def get_po_info_ajax(request):
    """Get detailed PO information"""
    po_id = request.GET.get('po_id')
    if not po_id:
        return JsonResponse({'success': False, 'error': 'PO ID required'})
    
    try:
        po = PurchaseOrder.objects.get(id=po_id, company=request.user.company)
        return JsonResponse({
            'success': True,
            'po_number': po.po_number,
            'po_date': po.po_date.strftime('%Y-%m-%d'),
            'total_amount': float(po.total_amount),
            'status': po.status,
            'supplier': po.supplier.name
        })
    except PurchaseOrder.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'PO not found'})


@login_required
def get_grn_info_ajax(request):
    """Get detailed GRN information"""
    grn_id = request.GET.get('grn_id')
    if not grn_id:
        return JsonResponse({'success': False, 'error': 'GRN ID required'})
    
    try:
        grn = GoodsReceiptNote.objects.get(id=grn_id, company=request.user.company)
        return JsonResponse({
            'success': True,
            'grn_number': grn.grn_number,
            'received_date': grn.received_date.strftime('%Y-%m-%d'),
            'status': grn.status,
            'item_count': grn.items.count(),
            'supplier': grn.supplier.name
        })
    except GoodsReceiptNote.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'GRN not found'})


@login_required
def get_po_items_ajax(request):
    """Get PO items for loading into bill"""
    po_id = request.GET.get('po_id')
    if not po_id:
        return JsonResponse({'success': False, 'error': 'PO ID required'})
    
    try:
        po = PurchaseOrder.objects.get(id=po_id, company=request.user.company)
        items = []
        
        for item in po.items.all():
            items.append({
                'id': item.id,
                'product_id': item.product.id,
                'product_name': item.product.name,
                'product_sku': item.product.sku,
                'quantity': float(item.quantity),
                'unit_price': float(item.unit_price),
                'line_total': float(item.line_total)
            })
        
        return JsonResponse({
            'success': True,
            'items': items
        })
    except PurchaseOrder.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'PO not found'})


@login_required
def get_grn_items_ajax(request):
    """Get GRN items for loading into bill"""
    grn_id = request.GET.get('grn_id')
    if not grn_id:
        return JsonResponse({'success': False, 'error': 'GRN ID required'})
    
    try:
        grn = GoodsReceiptNote.objects.get(id=grn_id, company=request.user.company)
        items = []
        
        for item in grn.items.all():
            tracking_items = []
            if item.tracking_items.exists():
                for tracking in item.tracking_items.all():
                    tracking_items.append({
                        'tracking_number': tracking.tracking_number,
                        'tracking_type': tracking.tracking_type,
                        'batch_number': tracking.batch_number,
                        'manufacturing_date': tracking.manufacturing_date.strftime('%Y-%m-%d') if tracking.manufacturing_date else None,
                        'expiry_date': tracking.expiry_date.strftime('%Y-%m-%d') if tracking.expiry_date else None,
                    })
            
            items.append({
                'id': item.id,
                'product_id': item.product.id,
                'product_name': item.product.name,
                'product_sku': item.product.sku,
                'received_qty': float(item.received_qty),
                'unit_price': float(item.po_item.unit_price) if item.po_item else 0,
                'po_item': {
                    'id': item.po_item.id,
                    'unit_price': float(item.po_item.unit_price)
                } if item.po_item else None,
                'tracking_items': tracking_items
            })
        
        return JsonResponse({
            'success': True,
            'items': items
        })
    except GoodsReceiptNote.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'GRN not found'})


@login_required 
def validate_matching_ajax(request):
    """Validate PO and GRN matching"""
    po_id = request.GET.get('po_id')
    grn_id = request.GET.get('grn_id')
    
    if not po_id or not grn_id:
        return JsonResponse({'success': False, 'error': 'Both PO and GRN IDs required'})
    
    try:
        po = PurchaseOrder.objects.get(id=po_id, company=request.user.company)
        grn = GoodsReceiptNote.objects.get(id=grn_id, company=request.user.company)
        
        errors = []
        
        # Check if GRN is from the selected PO
        if grn.purchase_order_id != int(po_id):
            errors.append('Selected GRN must be from the selected Purchase Order')
        
        # Check if both have the same supplier
        if po.supplier_id != grn.supplier_id:
            errors.append('PO and GRN must have the same supplier')
        
        return JsonResponse({
            'success': True,
            'is_valid': len(errors) == 0,
            'errors': errors
        })
        
    except (PurchaseOrder.DoesNotExist, GoodsReceiptNote.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Invalid PO or GRN'})


@login_required
def bill_approve_ajax(request, pk):
    """Approve a bill via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST method required'})
    
    try:
        bill = get_object_or_404(Bill, pk=pk, company=request.user.company)
        
        # Check permissions
        if not request.user.has_perm('purchase.approve_bill'):
            return JsonResponse({'success': False, 'message': 'You do not have permission to approve bills'})
        
        # Check if bill can be approved
        if bill.status != 'submitted':
            return JsonResponse({'success': False, 'message': 'Only submitted bills can be approved'})
        
        bill.status = 'approved'
        bill.approved_by = request.user
        bill.approved_at = timezone.now()
        bill.save()
        
        return JsonResponse({'success': True, 'message': 'Bill approved successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
def bill_delete_ajax(request, pk):
    """Delete a bill via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST method required'})
    
    try:
        bill = get_object_or_404(Bill, pk=pk, company=request.user.company)
        
        # Check if bill can be deleted
        if bill.status != 'draft':
            return JsonResponse({'success': False, 'message': 'Only draft bills can be deleted'})
        
        bill.delete()
        
        return JsonResponse({'success': True, 'message': 'Bill deleted successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
def reports_ui(request):
    """Purchase Reports Dashboard: Summary stats and monthly charts"""
    company = request.user.company

    # Summary stats
    total_purchase_orders = PurchaseOrder.objects.filter(company=company).count()
    total_goods_received = GoodsReceiptNote.objects.filter(company=company).count()
    total_returns = PurchaseReturn.objects.filter(company=company).count()
    active_suppliers = Supplier.objects.filter(company=company, is_active=True).count()

    # Calculate additional KPIs
    po_with_amounts = PurchaseOrder.objects.filter(company=company, total_amount__isnull=False)
    avg_order_value = po_with_amounts.aggregate(avg=Avg('total_amount'))['avg'] or 0

    # Calculate on-time delivery rate (mock data for now)
    on_time_delivery_rate = 94.5  # This would be calculated from actual delivery data

    # Calculate return rate
    if total_goods_received > 0:
        return_rate = (total_returns / total_goods_received) * 100
    else:
        return_rate = 0

    # Monthly Purchase Orders (last 12 months)
    from datetime import datetime, timedelta
    twelve_months_ago = datetime.now() - timedelta(days=365)
    
    po_months = (
        PurchaseOrder.objects.filter(company=company, created_at__gte=twelve_months_ago)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    monthly_po_labels = [m['month'].strftime('%b %Y') for m in po_months]
    monthly_po_data = [m['count'] for m in po_months]

    # Monthly Goods Received (last 12 months)
    grn_months = (
        GoodsReceiptNote.objects.filter(company=company, created_at__gte=twelve_months_ago)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    monthly_grn_labels = [m['month'].strftime('%b %Y') for m in grn_months]
    monthly_grn_data = [m['count'] for m in grn_months]

    # Monthly Returns (last 12 months)
    return_months = (
        PurchaseReturn.objects.filter(company=company, created_at__gte=twelve_months_ago)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    monthly_return_data = [m['count'] for m in return_months]

    # Align all months for GRN vs Returns chart
    all_months = sorted(set([m['month'] for m in grn_months] + [m['month'] for m in return_months]))
    monthly_goods_received_labels = [m.strftime('%b %Y') for m in all_months]
    grn_dict = {m['month']: m['count'] for m in grn_months}
    return_dict = {m['month']: m['count'] for m in return_months}
    monthly_goods_received_data = [grn_dict.get(month, 0) for month in all_months]
    monthly_returns_data = [return_dict.get(month, 0) for month in all_months]

    context = {
        'total_purchase_orders': total_purchase_orders,
        'total_goods_received': total_goods_received,
        'total_returns': total_returns,
        'active_suppliers': active_suppliers,
        'avg_order_value': avg_order_value,
        'on_time_delivery_rate': on_time_delivery_rate,
        'return_rate': return_rate,
        'monthly_purchase_orders_labels': monthly_po_labels,
        'monthly_purchase_orders_data': monthly_po_data,
        'monthly_goods_received_labels': monthly_goods_received_labels,
        'monthly_goods_received_data': monthly_goods_received_data,
        'monthly_returns_data': monthly_returns_data,
    }
    return render(request, 'purchase/reports.html', context)