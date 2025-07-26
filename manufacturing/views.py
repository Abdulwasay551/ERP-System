from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import BillOfMaterials
from django.views.decorators.http import require_POST

# Create your views here.

@login_required
def boms_ui(request):
    boms = BillOfMaterials.objects.filter(company=request.user.company)
    return render(request, 'manufacturing/boms-ui.html', {'boms': boms})

@login_required
@require_POST
def boms_add(request):
    name = request.POST.get('name')
    code = request.POST.get('code')
    description = request.POST.get('description')
    is_active = request.POST.get('is_active') == 'on'
    if not name or not code:
        return JsonResponse({'success': False, 'error': 'Name and code are required.'}, status=400)
    bom = BillOfMaterials.objects.create(
        company=request.user.company,
        name=name,
        code=code,
        description=description or '',
        is_active=is_active,
        created_by=request.user
    )
    return JsonResponse({
        'success': True,
        'bom': {
            'id': bom.id,
            'name': bom.name,
            'code': bom.code,
            'description': bom.description,
            'is_active': bom.is_active
        }
    })

@login_required
@require_POST
def boms_edit(request, pk):
    bom = get_object_or_404(BillOfMaterials, pk=pk, company=request.user.company)
    name = request.POST.get('name')
    code = request.POST.get('code')
    description = request.POST.get('description')
    is_active = request.POST.get('is_active') == 'on'
    if not name or not code:
        return JsonResponse({'success': False, 'error': 'Name and code are required.'}, status=400)
    bom.name = name
    bom.code = code
    bom.description = description or ''
    bom.is_active = is_active
    bom.save()
    return JsonResponse({
        'success': True,
        'bom': {
            'id': bom.id,
            'name': bom.name,
            'code': bom.code,
            'description': bom.description,
            'is_active': bom.is_active
        }
    })

@login_required
@require_POST
def boms_delete(request, pk):
    bom = get_object_or_404(BillOfMaterials, pk=pk, company=request.user.company)
    bom.delete()
    return JsonResponse({'success': True})

@login_required
def workorders_ui(request):
    return render(request, 'manufacturing/workorders-ui.html')

@login_required
def production_ui(request):
    return render(request, 'manufacturing/production-ui.html')

@login_required
def quality_ui(request):
    return render(request, 'manufacturing/quality-ui.html')
