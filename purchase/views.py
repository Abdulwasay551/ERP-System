from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import PurchaseOrder, Supplier
from django.views.decorators.http import require_POST

# Create your views here.

@login_required
def purchaseorders_ui(request):
    purchaseorders = PurchaseOrder.objects.filter(company=request.user.company)
    suppliers = Supplier.objects.filter(company=request.user.company)
    return render(request, 'purchase/purchaseorders-ui.html', {'purchaseorders': purchaseorders, 'suppliers': suppliers})

@login_required
@require_POST
def purchaseorders_add(request):
    order_number = request.POST.get('order_number')
    supplier_id = request.POST.get('supplier_id')
    order_date = request.POST.get('order_date')
    status = request.POST.get('status')
    if not order_number:
        return JsonResponse({'success': False, 'error': 'Order number is required.'}, status=400)
    supplier = Supplier.objects.filter(pk=supplier_id, company=request.user.company).first() if supplier_id else None
    po = PurchaseOrder.objects.create(
        company=request.user.company,
        order_number=order_number,
        supplier=supplier,
        order_date=order_date or None,
        status=status or '',
        created_by=request.user
    )
    return JsonResponse({
        'success': True,
        'purchaseorder': {
            'id': po.id,
            'order_number': po.order_number,
            'supplier': po.supplier.name if po.supplier else '',
            'supplier_id': po.supplier.id if po.supplier else '',
            'order_date': po.order_date or '',
            'status': po.status
        }
    })

@login_required
@require_POST
def purchaseorders_edit(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk, company=request.user.company)
    order_number = request.POST.get('order_number')
    supplier_id = request.POST.get('supplier_id')
    order_date = request.POST.get('order_date')
    status = request.POST.get('status')
    if not order_number:
        return JsonResponse({'success': False, 'error': 'Order number is required.'}, status=400)
    supplier = Supplier.objects.filter(pk=supplier_id, company=request.user.company).first() if supplier_id else None
    po.order_number = order_number
    po.supplier = supplier
    po.order_date = order_date or None
    po.status = status or ''
    po.save()
    return JsonResponse({
        'success': True,
        'purchaseorder': {
            'id': po.id,
            'order_number': po.order_number,
            'supplier': po.supplier.name if po.supplier else '',
            'supplier_id': po.supplier.id if po.supplier else '',
            'order_date': po.order_date or '',
            'status': po.status
        }
    })

@login_required
@require_POST
def purchaseorders_delete(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk, company=request.user.company)
    po.delete()
    return JsonResponse({'success': True})

@login_required
def suppliers_ui(request):
    suppliers = Supplier.objects.filter(company=request.user.company)
    return render(request, 'purchase/suppliers-ui.html', {'suppliers': suppliers})

@login_required
def bills_ui(request):
    # For now, just return a simple template
    return render(request, 'purchase/bills-ui.html')

@login_required
def payments_ui(request):
    # For now, just return a simple template
    return render(request, 'purchase/payments-ui.html')
