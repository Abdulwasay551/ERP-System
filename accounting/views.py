from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Account, AccountGroup
from django.views.decorators.http import require_POST

# Create your views here.

@login_required
def accounts_ui(request):
    accounts = Account.objects.filter(company=request.user.company)
    return render(request, 'accounting/accounts-ui.html', {'accounts': accounts})

@login_required
@require_POST
def accounts_add(request):
    code = request.POST.get('code')
    name = request.POST.get('name')
    type_ = request.POST.get('type')
    group_name = request.POST.get('group')
    is_active = request.POST.get('is_active') == 'on'
    if not code or not name or not type_ or not group_name:
        return JsonResponse({'success': False, 'error': 'Code, name, type, and group are required.'}, status=400)
    group = AccountGroup.objects.filter(company=request.user.company, name=group_name).first()
    if not group:
        return JsonResponse({'success': False, 'error': 'Group not found.'}, status=400)
    account = Account.objects.create(
        company=request.user.company,
        code=code,
        name=name,
        type=type_,
        group=group,
        is_active=is_active
    )
    return JsonResponse({
        'success': True,
        'account': {
            'id': account.id,
            'code': account.code,
            'name': account.name,
            'type': account.get_type_display(),
            'group': account.group.name,
            'is_active': account.is_active
        }
    })

@login_required
@require_POST
def accounts_edit(request, pk):
    account = get_object_or_404(Account, pk=pk, company=request.user.company)
    code = request.POST.get('code')
    name = request.POST.get('name')
    type_ = request.POST.get('type')
    group_name = request.POST.get('group')
    is_active = request.POST.get('is_active') == 'on'
    if not code or not name or not type_ or not group_name:
        return JsonResponse({'success': False, 'error': 'Code, name, type, and group are required.'}, status=400)
    group = AccountGroup.objects.filter(company=request.user.company, name=group_name).first()
    if not group:
        return JsonResponse({'success': False, 'error': 'Group not found.'}, status=400)
    account.code = code
    account.name = name
    account.type = type_
    account.group = group
    account.is_active = is_active
    account.save()
    return JsonResponse({
        'success': True,
        'account': {
            'id': account.id,
            'code': account.code,
            'name': account.name,
            'type': account.get_type_display(),
            'group': account.group.name,
            'is_active': account.is_active
        }
    })

@login_required
@require_POST
def accounts_delete(request, pk):
    account = get_object_or_404(Account, pk=pk, company=request.user.company)
    account.delete()
    return JsonResponse({'success': True})
